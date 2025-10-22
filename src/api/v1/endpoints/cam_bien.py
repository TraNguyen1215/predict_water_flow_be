from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from src.api import deps
from src.schemas.sensor import SensorCreate, SensorOut
from src.crud.cam_bien import create_cam_bien, list_cam_bien_for_user, get_cam_bien_by_id, update_cam_bien, delete_cam_bien

router = APIRouter()


@router.post("/", status_code=201, response_model=SensorOut)
async def create_cam_bien(
    payload: SensorCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo cảm biến mới"""
    ma = await create_cam_bien(db, current_user.ma_nguoi_dung, payload)
    await db.commit()
    return SensorOut(
        ma_cam_bien=ma,
        ten_cam_bien=payload.ten_cam_bien,
        mo_ta=payload.mo_ta,
        ngay_lap_dat=payload.ngay_lap_dat,
        ma_may_bom=payload.ma_may_bom,
        loai=payload.loai,
    )


@router.get("/", status_code=200)
async def list_cam_bien(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách cảm biến."""
    rows = await list_cam_bien_for_user(db, current_user.ma_nguoi_dung, limit, offset)
    items = [
        SensorOut(
            ma_cam_bien=r.ma_cam_bien,
            ten_cam_bien=r.ten_cam_bien,
            mo_ta=r.mo_ta,
            ngay_lap_dat=r.ngay_lap_dat,
            thoi_gian_tao=r.thoi_gian_tao,
            ma_may_bom=r.ma_may_bom,
            ten_may_bom=r.ten_may_bom,
            trang_thai=r.trang_thai,
            loai=r.loai,
            ten_loai_cam_bien=r.ten_loai_cam_bien,
        )
        for r in rows
    ]
    return {"data": items, "limit": limit, "offset": offset, "total": len(items)}


@router.get("/{ma_cam_bien}", status_code=200)
async def get_cam_bien(
    ma_cam_bien: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy thông tin cảm biến theo mã cảm biến."""
    r = await get_cam_bien_by_id(db, ma_cam_bien)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảm biến")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập dữ liệu người khác")
    
    return SensorOut(
        ma_cam_bien=r.ma_cam_bien,
        ten_cam_bien=r.ten_cam_bien,
        mo_ta=r.mo_ta,
        ngay_lap_dat=r.ngay_lap_dat,
        ma_may_bom=r.ma_may_bom,
        ten_may_bom=r.ten_may_bom,
        trang_thai=r.trang_thai,
        loai=r.loai,
        ten_loai_cam_bien=r.ten_loai_cam_bien,
    )


@router.put("/{ma_cam_bien}", status_code=200)
async def update_cam_bien(
    ma_cam_bien: int,
    payload: SensorCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật thông tin cảm biến."""
    r = await get_cam_bien_by_id(db, ma_cam_bien)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảm biến")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa cảm biến này")
    await update_cam_bien(db, ma_cam_bien, payload)
    await db.commit()
    return {"message": "Cập nhật cảm biến thành công", "ma_cam_bien": ma_cam_bien}


@router.delete("/{ma_cam_bien}", status_code=200)
async def delete_cam_bien(
    ma_cam_bien: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá cảm biến theo mã cảm biến."""
    r = await get_cam_bien_by_id(db, ma_cam_bien)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảm biến")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép xoá cảm biến này")

    await delete_cam_bien(db, ma_cam_bien)
    await db.commit()
    
    return {"message": "Xoá cảm biến thành công", "ma_cam_bien": ma_cam_bien}
