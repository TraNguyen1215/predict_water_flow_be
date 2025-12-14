from typing import Optional
import math
from uuid import UUID
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from src.api import deps
from src.schemas.thong_bao import ThongBaoCreate, ThongBaoUpdate, ThongBaoResponse
from src.crud import thong_bao as crud_thong_bao
from src.crud.may_bom import list_may_bom_for_user
from src.crud.nguoi_dung import list_users
from src.models.nhat_ky_may_bom import NhatKyMayBom
from src.models.du_lieu_cam_bien import DuLieuCamBien

router = APIRouter()


async def _generate_weekly_report(db: AsyncSession, ma_nguoi_dung, ma_may_bom: int):
    """Tính toán dữ liệu báo cáo hàng tuần"""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Thứ 2 tuần trước
    
    # Đếm số lần tưới trong tuần
    q_watering = (
        select(func.count())
        .select_from(NhatKyMayBom)
        .where(
            NhatKyMayBom.ma_may_bom == ma_may_bom,
            func.date(NhatKyMayBom.thoi_gian_bat) >= start_of_week,
            func.date(NhatKyMayBom.thoi_gian_bat) < today
        )
    )
    res_watering = await db.execute(q_watering)
    watering_count = res_watering.scalar() or 0
    
    # Tính trung bình độ ẩm trong tuần
    q_humidity = (
        text("""
            SELECT AVG(do_am) as avg_humidity FROM du_lieu_cam_bien 
            WHERE ma_may_bom = :ma_may_bom 
            AND DATE(thoi_gian_tao) >= :start_date
            AND DATE(thoi_gian_tao) < :end_date
        """)
    )
    res_humidity = await db.execute(q_humidity, {
        "ma_may_bom": ma_may_bom,
        "start_date": start_of_week,
        "end_date": today
    })
    humidity_row = res_humidity.fetchone()
    avg_humidity = humidity_row[0] if humidity_row and humidity_row[0] else 0
    
    # Tính tổng lưu lượng trong tuần
    q_flow = (
        text("""
            SELECT SUM(luu_luong_nuoc) as total_flow FROM du_lieu_cam_bien 
            WHERE ma_may_bom = :ma_may_bom 
            AND DATE(thoi_gian_tao) >= :start_date
            AND DATE(thoi_gian_tao) < :end_date
        """)
    )
    res_flow = await db.execute(q_flow, {
        "ma_may_bom": ma_may_bom,
        "start_date": start_of_week,
        "end_date": today
    })
    flow_row = res_flow.fetchone()
    total_flow = flow_row[0] if flow_row and flow_row[0] else 0
    
    return {
        "watering_count": watering_count,
        "avg_humidity": round(avg_humidity, 2) if avg_humidity else 0,
        "total_flow": round(total_flow, 2) if total_flow else 0,
        "period": f"{start_of_week} đến {today - timedelta(days=1)}"
    }


async def _generate_monthly_report(db: AsyncSession, ma_nguoi_dung, ma_may_bom: int):
    """Tính toán dữ liệu báo cáo hàng tháng"""
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    
    # Đếm số lần tưới trong tháng
    q_watering = (
        select(func.count())
        .select_from(NhatKyMayBom)
        .where(
            NhatKyMayBom.ma_may_bom == ma_may_bom,
            func.date(NhatKyMayBom.thoi_gian_bat) >= start_of_month,
            func.date(NhatKyMayBom.thoi_gian_bat) < today
        )
    )
    res_watering = await db.execute(q_watering)
    watering_count = res_watering.scalar() or 0
    
    # Tính trung bình độ ẩm trong tháng
    q_humidity = (
        text("""
            SELECT AVG(do_am) as avg_humidity FROM du_lieu_cam_bien 
            WHERE ma_may_bom = :ma_may_bom 
            AND DATE(thoi_gian_tao) >= :start_date
            AND DATE(thoi_gian_tao) < :end_date
        """)
    )
    res_humidity = await db.execute(q_humidity, {
        "ma_may_bom": ma_may_bom,
        "start_date": start_of_month,
        "end_date": today
    })
    humidity_row = res_humidity.fetchone()
    avg_humidity = humidity_row[0] if humidity_row and humidity_row[0] else 0
    
    # Tính tổng lưu lượng trong tháng
    q_flow = (
        text("""
            SELECT SUM(luu_luong_nuoc) as total_flow FROM du_lieu_cam_bien 
            WHERE ma_may_bom = :ma_may_bom 
            AND DATE(thoi_gian_tao) >= :start_date
            AND DATE(thoi_gian_tao) < :end_date
        """)
    )
    res_flow = await db.execute(q_flow, {
        "ma_may_bom": ma_may_bom,
        "start_date": start_of_month,
        "end_date": today
    })
    flow_row = res_flow.fetchone()
    total_flow = flow_row[0] if flow_row and flow_row[0] else 0
    
    return {
        "watering_count": watering_count,
        "avg_humidity": round(avg_humidity, 2) if avg_humidity else 0,
        "total_flow": round(total_flow, 2) if total_flow else 0,
        "period": f"Tháng {today.month}/{today.year}"
    }


@router.post("/", status_code=201, response_model=ThongBaoResponse)
async def create_thong_bao(
    payload: ThongBaoCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo thông báo mới"""
    thong_bao = await crud_thong_bao.create(db, payload)
    return thong_bao


@router.get("/", status_code=200)
async def get_thong_bao_list(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy danh sách thông báo của người dùng"""
    if page is not None:
        offset = (page - 1) * limit

    thong_baos, total = await crud_thong_bao.get_by_user(
        db, current_user.ma_nguoi_dung, skip=offset, limit=limit
    )
    
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    
    return {
        "data": thong_baos,
        "limit": limit,
        "offset": offset,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    }


@router.get("/user/{ma_nguoi_dung}", status_code=200)
async def get_thong_bao_by_user(
    ma_nguoi_dung: UUID,
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy danh sách thông báo theo ma_nguoi_dung (Dành cho admin hoặc chính chủ)"""
    if current_user.ma_nguoi_dung != ma_nguoi_dung and not getattr(current_user, "quan_tri_vien", False):
         raise HTTPException(status_code=403, detail="Bạn không có quyền xem thông báo của người khác")

    if page is not None:
        offset = (page - 1) * limit

    thong_baos, total = await crud_thong_bao.get_by_user(
        db, ma_nguoi_dung, skip=offset, limit=limit
    )
    
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    
    return {
        "data": thong_baos,
        "limit": limit,
        "offset": offset,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    }


@router.get("/unread", status_code=200)
async def get_unread_thong_bao(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy danh sách thông báo chưa xem"""
    if page is not None:
        offset = (page - 1) * limit

    thong_baos, total = await crud_thong_bao.get_unread_by_user(
        db, current_user.ma_nguoi_dung, skip=offset, limit=limit
    )
    
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    
    return {
        "data": thong_baos,
        "limit": limit,
        "offset": offset,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    }


@router.get("/count-unread", status_code=200)
async def count_unread_thong_bao(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Đếm số thông báo chưa xem"""
    count = await crud_thong_bao.count_unread_by_user(db, current_user.ma_nguoi_dung)
    return {"count": count}


@router.get("/{ma_thong_bao}", status_code=200, response_model=ThongBaoResponse)
async def get_thong_bao_detail(
    ma_thong_bao: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy chi tiết thông báo"""
    thong_bao = await crud_thong_bao.get_by_id(db, ma_thong_bao)
    if not thong_bao:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")

    if thong_bao.ma_nguoi_dung != current_user.ma_nguoi_dung and thong_bao.ma_nguoi_dung is not None:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem thông báo này")

    return thong_bao


@router.put("/{ma_thong_bao}", status_code=200, response_model=ThongBaoResponse)
async def update_thong_bao(
    ma_thong_bao: int,
    payload: ThongBaoUpdate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật thông báo"""
    thong_bao = await crud_thong_bao.get_by_id(db, ma_thong_bao)
    if not thong_bao:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")

    if thong_bao.ma_nguoi_dung != current_user.ma_nguoi_dung:
        raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật thông báo này")

    updated = await crud_thong_bao.update(db, ma_thong_bao, payload)
    return updated


@router.post("/{ma_thong_bao}/mark-as-read", status_code=200, response_model=ThongBaoResponse)
async def mark_as_read(
    ma_thong_bao: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Đánh dấu thông báo đã xem"""
    thong_bao = await crud_thong_bao.get_by_id(db, ma_thong_bao)
    if not thong_bao:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")

    if thong_bao.ma_nguoi_dung != current_user.ma_nguoi_dung and thong_bao.ma_nguoi_dung is not None:
        raise HTTPException(status_code=403, detail="Bạn không có quyền đánh dấu thông báo này")

    updated = await crud_thong_bao.mark_as_read(db, ma_thong_bao)
    return updated


@router.post("/mark-all-as-read", status_code=200)
async def mark_all_as_read(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Đánh dấu tất cả thông báo đã xem"""
    count = await crud_thong_bao.mark_all_as_read(db, current_user.ma_nguoi_dung)
    return {"count": count}


@router.delete("/delete-all", status_code=200)
async def delete_all_thong_bao(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá tất cả thông báo của người dùng"""
    count = await crud_thong_bao.delete_by_user(db, current_user.ma_nguoi_dung)
    return {"deleted_count": count}


@router.delete("/{ma_thong_bao}", status_code=200)
async def delete_thong_bao(
    ma_thong_bao: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá thông báo"""
    thong_bao = await crud_thong_bao.get_by_id(db, ma_thong_bao)
    if not thong_bao:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")

    if thong_bao.ma_nguoi_dung != current_user.ma_nguoi_dung:
        if thong_bao.ma_nguoi_dung is None and getattr(current_user, "quan_tri_vien", False):
            pass
        else:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xoá thông báo này")

    success = await crud_thong_bao.delete(db, ma_thong_bao)
    return {"deleted": success}


@router.post("/send-weekly-reports", status_code=200)
async def send_weekly_reports(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Gửi báo cáo hàng tuần cho tất cả người dùng. Chỉ admin mới có quyền."""
    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới có quyền gửi báo cáo")
    
    # Lấy tất cả người dùng
    users, total, _, _, _, _ = await list_users(db, limit=10000, offset=0)
    
    sent_count = 0
    for user in users:
        # Lấy danh sách máy bơm của user
        pumps, _ = await list_may_bom_for_user(db, user.ma_nguoi_dung, limit=100, offset=0)
        
        if pumps:
            report_content = "📊 **Báo cáo tuần**\n\n"
            
            for pump in pumps:
                weekly_data = await _generate_weekly_report(db, user.ma_nguoi_dung, pump.ma_may_bom)
                report_content += f"**Thiết bị: {pump.ten_may_bom}**\n"
                report_content += f"- Số lần tưới: {weekly_data['watering_count']} lần\n"
                report_content += f"- Độ ẩm trung bình: {weekly_data['avg_humidity']}%\n"
                report_content += f"- Tổng lưu lượng: {weekly_data['total_flow']} lít\n"
                report_content += f"- Kỳ: {weekly_data['period']}\n\n"
            
            # Gửi thông báo
            await crud_thong_bao.create_notification(
                db=db,
                ma_nguoi_dung=user.ma_nguoi_dung,
                loai="INFO",
                muc_do="MEDIUM",
                tieu_de="Báo cáo tuần của bạn",
                noi_dung=report_content,
                du_lieu_lien_quan={"type": "weekly_report"}
            )
            sent_count += 1
    
    await db.commit()
    return {"message": f"Gửi báo cáo hàng tuần thành công cho {sent_count} người dùng"}


@router.post("/send-monthly-reports", status_code=200)
async def send_monthly_reports(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Gửi báo cáo hàng tháng cho tất cả người dùng. Chỉ admin mới có quyền."""
    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới có quyền gửi báo cáo")
    
    # Lấy tất cả người dùng
    users, total, _, _, _, _ = await list_users(db, limit=10000, offset=0)
    
    sent_count = 0
    for user in users:
        # Lấy danh sách máy bơm của user
        pumps, _ = await list_may_bom_for_user(db, user.ma_nguoi_dung, limit=100, offset=0)
        
        if pumps:
            report_content = "📊 **Báo cáo tháng**\n\n"
            
            for pump in pumps:
                monthly_data = await _generate_monthly_report(db, user.ma_nguoi_dung, pump.ma_may_bom)
                report_content += f"**Thiết bị: {pump.ten_may_bom}**\n"
                report_content += f"- Số lần tưới: {monthly_data['watering_count']} lần\n"
                report_content += f"- Độ ẩm trung bình: {monthly_data['avg_humidity']}%\n"
                report_content += f"- Tổng lưu lượng: {monthly_data['total_flow']} lít\n"
                report_content += f"- Kỳ: {monthly_data['period']}\n\n"
            
            # Gửi thông báo
            await crud_thong_bao.create_notification(
                db=db,
                ma_nguoi_dung=user.ma_nguoi_dung,
                loai="INFO",
                muc_do="MEDIUM",
                tieu_de="Báo cáo tháng của bạn",
                noi_dung=report_content,
                du_lieu_lien_quan={"type": "monthly_report"}
            )
            sent_count += 1
    
    await db.commit()
    return {"message": f"Gửi báo cáo hàng tháng thành công cho {sent_count} người dùng"}
