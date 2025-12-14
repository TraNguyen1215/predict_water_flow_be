from datetime import date, datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from src.api import deps
from src.schemas.nhat_ky import NhatKyCreate, NhatKyOut
from src.crud.nhat_ky_may_bom import create_nhat_ky, list_nhat_ky_for_pump, get_nhat_ky_by_id, update_nhat_ky, delete_nhat_ky
from src.crud.may_bom import get_may_bom_by_id
from src.crud.thong_bao import create_notification
from src.models.nhat_ky_may_bom import NhatKyMayBom
from src.models.du_lieu_cam_bien import DuLieuCamBien

router = APIRouter()


async def _check_abnormal_watering_frequency(db: AsyncSession, ma_may_bom: int, ma_nguoi_dung):
    """Kiểm tra nếu có nhiều lần tưới bất thường trong ngày"""
    today = date.today()
    
    # Đếm số lần tưới hôm nay
    q = (
        select(func.count())
        .select_from(NhatKyMayBom)
        .where(
            NhatKyMayBom.ma_may_bom == ma_may_bom,
            func.date(NhatKyMayBom.thoi_gian_bat) == today
        )
    )
    res = await db.execute(q)
    watering_count = res.scalar() or 0
    
    # Nếu có hơn 5 lần tưới trong ngày, cảnh báo
    if watering_count > 5:
        pump = await get_may_bom_by_id(db, ma_may_bom)
        pump_name = pump.ten_may_bom if pump else f"Thiết bị {ma_may_bom}"
        await create_notification(
            db=db,
            ma_nguoi_dung=ma_nguoi_dung,
            loai="ALERT",
            muc_do="MEDIUM",
            tieu_de="Nhiều lần tưới bất thường",
            noi_dung=f"Thiết bị '{pump_name}' đã tưới {watering_count} lần trong hôm nay. Vui lòng kiểm tra cấu hình hệ thống tưới.",
            ma_thiet_bi=ma_may_bom,
            du_lieu_lien_quan={"ma_may_bom": ma_may_bom, "so_lan_tuoi": watering_count}
        )


async def _check_watering_frequency_increase(db: AsyncSession, ma_may_bom: int, ma_nguoi_dung):
    """Kiểm tra nếu tần suất tưới tăng hơn bình thường"""
    today = date.today()
    
    # Đếm số lần tưới hôm nay
    q_today = (
        select(func.count())
        .select_from(NhatKyMayBom)
        .where(
            NhatKyMayBom.ma_may_bom == ma_may_bom,
            func.date(NhatKyMayBom.thoi_gian_bat) == today
        )
    )
    res_today = await db.execute(q_today)
    today_count = res_today.scalar() or 0
    
    # Lấy trung bình số lần tưới mỗi ngày trong 7 ngày gần đây (không tính hôm nay)
    seven_days_ago = today - timedelta(days=7)
    q_avg = (
        select(func.avg(func.count(NhatKyMayBom.ma_nhat_ky)))
        .select_from(NhatKyMayBom)
        .where(
            NhatKyMayBom.ma_may_bom == ma_may_bom,
            func.date(NhatKyMayBom.thoi_gian_bat) >= seven_days_ago,
            func.date(NhatKyMayBom.thoi_gian_bat) < today
        )
        .group_by(func.date(NhatKyMayBom.thoi_gian_bat))
    )
    res_avg = await db.execute(q_avg)
    avg_records = res_avg.fetchall()
    avg_count = sum(r[0] for r in avg_records if r[0]) / len(avg_records) if avg_records else 0
    
    # Nếu số lần tưới hôm nay tăng hơn 50% so với trung bình
    if avg_count > 0 and today_count > (avg_count * 1.5):
        pump = await get_may_bom_by_id(db, ma_may_bom)
        pump_name = pump.ten_may_bom if pump else f"Thiết bị {ma_may_bom}"
        await create_notification(
            db=db,
            ma_nguoi_dung=ma_nguoi_dung,
            loai="WARNING",
            muc_do="MEDIUM",
            tieu_de="Tần suất tưới tăng hơn bình thường",
            noi_dung=f"Thiết bị '{pump_name}' đã tưới {today_count} lần hôm nay, nhiều hơn bình thường ({avg_count:.1f} lần/ngày). Vui lòng kiểm tra cấu hình.",
            ma_thiet_bi=ma_may_bom,
            du_lieu_lien_quan={"ma_may_bom": ma_may_bom, "today_count": today_count, "avg_count": avg_count}
        )


async def _send_daily_watering_report(db: AsyncSession, ma_may_bom: int, ma_nguoi_dung):
    """Gửi thông báo INFO hàng ngày về tổng lượng nước tưới của ngày"""
    today = date.today()
    
    # Tính tổng lượng nước tưới hôm nay
    q = text("""
        SELECT SUM(COALESCE(du_lieu_cam_bien.luu_luong, 0)) as tong_luong_nuoc
        FROM nhat_ky_may_bom
        LEFT JOIN du_lieu_cam_bien ON nhat_ky_may_bom.ma_nhat_ky = du_lieu_cam_bien.ma_nhat_ky
        WHERE nhat_ky_may_bom.ma_may_bom = :ma_may_bom
        AND DATE(nhat_ky_may_bom.thoi_gian_bat) = :today
    """)
    
    result = await db.execute(q, {"ma_may_bom": ma_may_bom, "today": today})
    total_water = result.scalar() or 0
    
    pump = await get_may_bom_by_id(db, ma_may_bom)
    pump_name = pump.ten_may_bom if pump else f"Thiết bị {ma_may_bom}"
    
    await create_notification(
        db=db,
        ma_nguoi_dung=ma_nguoi_dung,
        loai="INFO",
        muc_do="LOW",
        tieu_de="Tổng lượng nước tưới ngày hôm nay",
        noi_dung=f"Thiết bị '{pump_name}' đã tưới tổng cộng {total_water:.2f} đơn vị nước hôm nay.",
        ma_thiet_bi=ma_may_bom,
        du_lieu_lien_quan={"ma_may_bom": ma_may_bom, "tong_luong_nuoc": total_water, "ngay": today.isoformat()}
    )


@router.post("/", status_code=201, response_model=NhatKyOut)
async def create_nhat_ky_endpoint(
    payload: NhatKyCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo nhật ký cho máy bơm (chỉ chủ sở hữu)."""
    
    pump = await get_may_bom_by_id(db, payload.ma_may_bom)
    if not pump:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép tạo nhật ký cho máy bơm này")

    obj = await create_nhat_ky(db, payload)
    await db.commit()
    
    # Kiểm tra cảnh báo tưới bất thường
    await _check_abnormal_watering_frequency(db, payload.ma_may_bom, current_user.ma_nguoi_dung)
    # Kiểm tra tần suất tưới tăng
    await _check_watering_frequency_increase(db, payload.ma_may_bom, current_user.ma_nguoi_dung)
    # Gửi thông báo tổng lượng nước tưới hôm nay
    await _send_daily_watering_report(db, payload.ma_may_bom, current_user.ma_nguoi_dung)
    await db.commit()
    
    return NhatKyOut(
        ma_nhat_ky=getattr(obj, "ma_nhat_ky"), # getattr(obj, "ma_nhat_ky", None),: là để tránh lỗi nếu obj không có thuộc tính ma_nhat_ky
        ma_may_bom=getattr(obj, "ma_may_bom", None),
        thoi_gian_bat=getattr(obj, "thoi_gian_bat", None),
        thoi_gian_tat=getattr(obj, "thoi_gian_tat", None),
        ghi_chu=getattr(obj, "ghi_chu", None),
        thoi_gian_tao=getattr(obj, "thoi_gian_tao"),
    )


@router.get("/ngay/{ngay}", status_code=200)
async def list_nhat_ky_endpoint(
    ngay: date,
    ma_may_bom: int = Query(...),
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách nhật ký cho một máy bơm (chỉ chủ sở hữu).
    """
    
    pump = await get_may_bom_by_id(db, ma_may_bom)
    if not pump:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập nhật ký của máy bơm này")

    if page is not None:
        offset = (page - 1) * limit

    rows, total = await list_nhat_ky_for_pump(db, ngay, ma_may_bom, limit, offset)
    items = [
        NhatKyOut(ma_nhat_ky=r.ma_nhat_ky, ma_may_bom=r.ma_may_bom, thoi_gian_bat=r.thoi_gian_bat, thoi_gian_tat=r.thoi_gian_tat, ghi_chu=r.ghi_chu, thoi_gian_tao=r.thoi_gian_tao)
        for r in rows
    ]

    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    return {"data": items, "limit": limit, "offset": offset, "page": page, "total_pages": total_pages, "total": total}


@router.get("/{ma_nhat_ky}", status_code=200)
async def get_nhat_ky_endpoint(
    ma_nhat_ky: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy thông tin nhật ký theo mã nhật ký (chỉ chủ sở hữu)."""
    
    r = await get_nhat_ky_by_id(db, ma_nhat_ky)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký")
    pump = await get_may_bom_by_id(db, r.ma_may_bom)
    if not pump:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm liên quan")
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập nhật ký của người khác")

    return NhatKyOut(ma_nhat_ky=r.ma_nhat_ky, ma_may_bom=r.ma_may_bom, thoi_gian_bat=r.thoi_gian_bat, thoi_gian_tat=r.thoi_gian_tat, ghi_chu=r.ghi_chu, thoi_gian_tao=r.thoi_gian_tao)

@router.put("/{ma_nhat_ky}", status_code=200)
async def update_nhat_ky_endpoint(
    ma_nhat_ky: int,
    payload: NhatKyCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật nhật ký (chỉ chủ sở hữu)."""
    
    r = await get_nhat_ky_by_id(db, ma_nhat_ky)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký")
    pump = await get_may_bom_by_id(db, r.ma_may_bom)
    if not pump:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm liên quan")
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa nhật ký của người khác")

    await update_nhat_ky(db, ma_nhat_ky, payload)
    await db.commit()
    
    return {"message": "Cập nhật nhật ký thành công", "ma_nhat_ky": ma_nhat_ky}


@router.delete("/{ma_nhat_ky}", status_code=200)
async def delete_nhat_ky_endpoint(
    ma_nhat_ky: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá nhật ký (chỉ chủ sở hữu)."""
    
    r = await get_nhat_ky_by_id(db, ma_nhat_ky)

    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký")
    pump = await get_may_bom_by_id(db, r.ma_may_bom)
    if not pump:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm liên quan")
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép xoá nhật ký của người khác")

    await delete_nhat_ky(db, ma_nhat_ky)
    await db.commit()
    
    return {"message": "Xoá nhật ký thành công", "ma_nhat_ky": ma_nhat_ky}
