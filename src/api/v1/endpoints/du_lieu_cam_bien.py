from datetime import date, datetime, timedelta
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.schemas.data import DataOut, DataCreate
from src.crud.du_lieu_cam_bien import (
    list_du_lieu_for_user,
    list_du_lieu_by_day,
    list_du_lieu_by_day_paginated,
    get_du_lieu_by_id,
    update_du_lieu,
)
from src.crud.may_bom import get_may_bom_by_id
from src.crud.thong_bao import create_notification
from src.api.v1.endpoints.admin_alerts import send_alert_to_admins_for_user_device_error

router = APIRouter()


async def _check_sensor_data_timeout(db: AsyncSession, ma_may_bom: int, ma_nguoi_dung: uuid.UUID):
    """Kiểm tra nếu cảm biến không có dữ liệu trong >5 phút"""
    # Lấy dữ liệu cảm biến gần nhất
    from sqlalchemy import desc
    q = (
        text("""
            SELECT thoi_gian_tao FROM du_lieu_cam_bien 
            WHERE ma_may_bom = :ma_may_bom 
            ORDER BY thoi_gian_tao DESC 
            LIMIT 1
        """)
    )
    res = await db.execute(q, {"ma_may_bom": ma_may_bom})
    last_data_time = res.scalar()
    
    if last_data_time:
        time_diff = datetime.utcnow() - last_data_time
        if time_diff.total_seconds() > 300:  # 5 phút = 300 giây
            pump = await get_may_bom_by_id(db, ma_may_bom)
            pump_name = pump.ten_may_bom if pump else f"Thiết bị {ma_may_bom}"
            await create_notification(
                db=db,
                ma_nguoi_dung=ma_nguoi_dung,
                loai="ALERT",
                muc_do="HIGH",
                tieu_de="Cảm biến mất dữ liệu",
                noi_dung=f"Cảm biến của thiết bị '{pump_name}' không có dữ liệu trong hơn 5 phút. Vui lòng kiểm tra kết nối thiết bị.",
                ma_thiet_bi=ma_may_bom,
                du_lieu_lien_quan={"ma_may_bom": ma_may_bom, "thoi_gian_cuoi": str(last_data_time)}
            )
            # Gửi alert tới admin
            await send_alert_to_admins_for_user_device_error(
                db=db,
                ma_may_bom=ma_may_bom,
                error_type="sensor_timeout",
                error_details=f"Cảm biến không có dữ liệu trong hơn 5 phút (lần cuối: {last_data_time})"
            )


async def _check_abnormal_flow(db: AsyncSession, ma_may_bom: int, ma_nguoi_dung: uuid.UUID, luu_luong_nuoc: Optional[float]):
    """Kiểm tra nếu lưu lượng tưới bất thường"""
    if luu_luong_nuoc is None or luu_luong_nuoc < 0:
        pump = await get_may_bom_by_id(db, ma_may_bom)
        pump_name = pump.ten_may_bom if pump else f"Thiết bị {ma_may_bom}"
        await create_notification(
            db=db,
            ma_nguoi_dung=ma_nguoi_dung,
            loai="ALERT",
            muc_do="MEDIUM",
            tieu_de="Lưu lượng nước bất thường",
            noi_dung=f"Thiết bị '{pump_name}' ghi nhận lưu lượng nước bất thường. Vui lòng kiểm tra lại.",
            ma_thiet_bi=ma_may_bom,
            du_lieu_lien_quan={"ma_may_bom": ma_may_bom, "luu_luong_nuoc": luu_luong_nuoc}
        )
        # Gửi alert tới admin
        await send_alert_to_admins_for_user_device_error(
            db=db,
            ma_may_bom=ma_may_bom,
            error_type="abnormal_flow",
            error_details=f"Lưu lượng nước bất thường: {luu_luong_nuoc}"
        )


async def _check_humidity_trend(db: AsyncSession, ma_may_bom: int, ma_nguoi_dung: uuid.UUID):
    """Kiểm tra xu hướng độ ẩm giảm trong 30 phút"""
    from sqlalchemy import desc
    thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
    
    # Lấy dữ liệu độ ẩm từ 30 phút trước
    q = (
        text("""
            SELECT do_am, thoi_gian_tao FROM du_lieu_cam_bien 
            WHERE ma_may_bom = :ma_may_bom 
            AND thoi_gian_tao >= :thirty_minutes_ago
            ORDER BY thoi_gian_tao ASC
        """)
    )
    res = await db.execute(q, {"ma_may_bom": ma_may_bom, "thirty_minutes_ago": thirty_minutes_ago})
    humidity_data = res.fetchall()
    
    if len(humidity_data) >= 2:
        first_humidity = humidity_data[0][0]
        last_humidity = humidity_data[-1][0]
        
        # Nếu độ ẩm giảm hơn 10% trong 30 phút
        if first_humidity is not None and last_humidity is not None and (first_humidity - last_humidity) > 10:
            pump = await get_may_bom_by_id(db, ma_may_bom)
            pump_name = pump.ten_may_bom if pump else f"Thiết bị {ma_may_bom}"
            await create_notification(
                db=db,
                ma_nguoi_dung=ma_nguoi_dung,
                loai="WARNING",
                muc_do="MEDIUM",
                tieu_de="Xu hướng độ ẩm giảm",
                noi_dung=f"Độ ẩm đất của thiết bị '{pump_name}' đang giảm nhanh trong 30 phút gần đây (từ {first_humidity}% xuống {last_humidity}%). Cây có thể đang khô nước.",
                ma_thiet_bi=ma_may_bom,
                du_lieu_lien_quan={"ma_may_bom": ma_may_bom, "humidity_start": first_humidity, "humidity_end": last_humidity}
            )


async def _check_flow_decrease_trend(db: AsyncSession, ma_may_bom: int, ma_nguoi_dung: uuid.UUID, current_flow: Optional[float]):
    """Kiểm tra xu hướng lưu lượng giảm so với trung bình"""
    if current_flow is None or current_flow < 0:
        return
    
    # Lấy trung bình lưu lượng trong 7 ngày gần đây
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    q = (
        text("""
            SELECT AVG(luu_luong_nuoc) as avg_flow FROM du_lieu_cam_bien 
            WHERE ma_may_bom = :ma_may_bom 
            AND thoi_gian_tao >= :seven_days_ago
            AND luu_luong_nuoc > 0
        """)
    )
    res = await db.execute(q, {"ma_may_bom": ma_may_bom, "seven_days_ago": seven_days_ago})
    avg_flow_row = res.fetchone()
    avg_flow = avg_flow_row[0] if avg_flow_row and avg_flow_row[0] else 0
    
    # Nếu lưu lượng hiện tại kém 30% so với trung bình
    if avg_flow > 0 and current_flow < (avg_flow * 0.7):
        pump = await get_may_bom_by_id(db, ma_may_bom)
        pump_name = pump.ten_may_bom if pump else f"Thiết bị {ma_may_bom}"
        await create_notification(
            db=db,
            ma_nguoi_dung=ma_nguoi_dung,
            loai="WARNING",
            muc_do="MEDIUM",
            tieu_de="Xu hướng lưu lượng giảm",
            noi_dung=f"Lưu lượng nước của thiết bị '{pump_name}' đang giảm so với bình thường (hiện tại: {current_flow}, trung bình: {avg_flow:.1f}). Có thể có vấn đề với hệ thống tưới.",
            ma_thiet_bi=ma_may_bom,
            du_lieu_lien_quan={"ma_may_bom": ma_may_bom, "current_flow": current_flow, "avg_flow": avg_flow}
        )


@router.get("/", status_code=200)
async def list_du_lieu(
    ma_may_bom: Optional[int] = Query(None),
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách dữ liệu cảm biến cho các máy bơm của người dùng đã xác thực. Tùy chọn lọc theo `ma_may_bom`."""
    if ma_may_bom:
        pump = await get_may_bom_by_id(db, ma_may_bom)
        if not pump:
            raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
        if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
            raise HTTPException(status_code=403, detail="Không được phép truy cập dữ liệu của máy bơm này")

    if page is not None:
        offset = (page - 1) * limit
        
    #nếu limit<0 lấy tất cả dữ liệu
    if limit < 0:
        limit = None

    rows, total = await list_du_lieu_for_user(db, current_user.ma_nguoi_dung, ma_may_bom, limit, offset)
    items = [
        DataOut(
            ma_du_lieu=r.ma_du_lieu,
            ma_may_bom=r.ma_may_bom,
            ma_nguoi_dung=str(r.ma_nguoi_dung) if r.ma_nguoi_dung is not None else None,
            ngay=r.ngay,
            luu_luong_nuoc=r.luu_luong_nuoc,
            do_am_dat=r.do_am_dat,
            nhiet_do=r.nhiet_do,
            do_am=r.do_am,
            mua=r.mua,
            so_xung=r.so_xung,
            tong_the_tich=r.tong_the_tich,
            thoi_gian_tao=r.thoi_gian_tao,
        )
        for r in rows
    ]
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    return {"data": items, "limit": limit, "offset": offset, "page": page, "total_pages": total_pages, "total": total}

@router.get("/ngay/{ngay}", status_code=200)
async def get_du_lieu_theo_ngay(
    ngay: date,
    ma_may_bom: int = Query(None),
    limit: int = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy dữ liệu cảm biến theo ngày cho tất cả các máy bơm của người dùng đã xác thực."""
    if ma_may_bom:
        pump = await get_may_bom_by_id(db, ma_may_bom)
        if not pump:
            raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
        if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
            raise HTTPException(status_code=403, detail="Không được phép truy cập dữ liệu của máy bơm này")

    if limit is None:
        rows = await list_du_lieu_by_day(db, current_user.ma_nguoi_dung, ngay, ma_may_bom)
        items = [
            DataOut(
                ma_du_lieu=r.ma_du_lieu,
                ma_may_bom=r.ma_may_bom,
                ma_nguoi_dung=str(r.ma_nguoi_dung) if r.ma_nguoi_dung is not None else None,
                ngay=r.ngay,
                luu_luong_nuoc=r.luu_luong_nuoc,
                do_am_dat=r.do_am_dat,
                nhiet_do=r.nhiet_do,
                do_am=r.do_am,
                mua=r.mua,
                so_xung=r.so_xung,
                tong_the_tich=r.tong_the_tich,
                thoi_gian_tao=r.thoi_gian_tao,
            )
            for r in rows
        ]
        return {"data": items, "total": len(items)}
    else:
        if page is not None:
            offset = (page - 1) * limit
        rows, total = await list_du_lieu_by_day_paginated(db, current_user.ma_nguoi_dung, ngay, ma_may_bom, limit, offset)
        items = [
            DataOut(
                ma_du_lieu=r.ma_du_lieu,
                ma_may_bom=r.ma_may_bom,
                ma_nguoi_dung=str(r.ma_nguoi_dung) if r.ma_nguoi_dung is not None else None,
                ngay=r.ngay,
                luu_luong_nuoc=r.luu_luong_nuoc,
                do_am_dat=r.do_am_dat,
                nhiet_do=r.nhiet_do,
                do_am=r.do_am,
                mua=r.mua,
                so_xung=r.so_xung,
                tong_the_tich=r.tong_the_tich,
                thoi_gian_tao=r.thoi_gian_tao,
            )
            for r in rows
        ]
        page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = math.ceil(total / limit) if limit > 0 else 1
        return {"data": items, "limit": limit, "offset": offset, "page": page, "total_pages": total_pages, "total": total}


@router.put("/{ma_du_lieu}", status_code=200)
async def update_du_lieu(
    ma_du_lieu: int,
    payload: DataCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật dữ liệu cảm biến theo mã dữ liệu cảm biến."""
    
    r = await get_du_lieu_by_id(db, ma_du_lieu)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa dữ liệu của người khác")

    updates = {}
    if getattr(payload, "ngay", None) is not None:
        updates["ngay"] = payload.ngay
    if getattr(payload, "luu_luong_nuoc", None) is not None:
        updates["luu_luong_nuoc"] = payload.luu_luong_nuoc
    if getattr(payload, "do_am_dat", None) is not None:
        updates["do_am_dat"] = payload.do_am_dat
    if getattr(payload, "nhiet_do", None) is not None:
        updates["nhiet_do"] = payload.nhiet_do
    if getattr(payload, "do_am", None) is not None:
        updates["do_am"] = payload.do_am
    if getattr(payload, "mua", None) is not None:
        updates["mua"] = payload.mua
    if getattr(payload, "so_xung", None) is not None:
        updates["so_xung"] = payload.so_xung
    if getattr(payload, "tong_the_tich", None) is not None:
        updates["tong_the_tich"] = payload.tong_the_tich

    if not updates:
        return {"message": "Không có trường nào để cập nhật"}

    await update_du_lieu(db, ma_du_lieu, updates)
    await db.commit()
    
    # Kiểm tra cảnh báo
    r = await get_du_lieu_by_id(db, ma_du_lieu)
    if r:
        # Kiểm tra timeout cảm biến
        await _check_sensor_data_timeout(db, r.ma_may_bom, r.ma_nguoi_dung)
        # Kiểm tra lưu lượng bất thường
        if getattr(payload, "luu_luong_nuoc", None) is not None:
            await _check_abnormal_flow(db, r.ma_may_bom, r.ma_nguoi_dung, payload.luu_luong_nuoc)
            # Kiểm tra xu hướng lưu lượng giảm
            await _check_flow_decrease_trend(db, r.ma_may_bom, r.ma_nguoi_dung, payload.luu_luong_nuoc)
        # Kiểm tra xu hướng độ ẩm giảm
        await _check_humidity_trend(db, r.ma_may_bom, r.ma_nguoi_dung)
        await db.commit()
    
    return {"message": "Cập nhật dữ liệu thành công", "ma_du_lieu": ma_du_lieu}
