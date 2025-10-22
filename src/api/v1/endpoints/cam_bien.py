from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from src.api import deps
from src.schemas.sensor import SensorCreate, SensorOut
from src.crud.cam_bien import *
from src.models.cam_bien import CamBien


def _extract(row, key):
    """Safely extract a value from a mapping, Row, or ORM instance.

    Returns a primitive (int/str/datetime) when possible. If the value
    is an ORM object (like a CamBien), try to return its scalar id attribute.
    """
    # mapping-like (dict or RowMapping)
    try:
        if hasattr(row, "get"):
            val = row.get(key)
        else:
            val = getattr(row, key)
    except Exception:
        # fallback to indexing
        try:
            val = row[key]
        except Exception:
            val = None

    # if value is an ORM instance, try to extract scalar id attribute
    if isinstance(val, CamBien):
        return getattr(val, "ma_cam_bien", None)
    return val

router = APIRouter()


@router.post("/", status_code=201, response_model=SensorOut)
async def create_cam_bien_endpoint(
    payload: SensorCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo cảm biến mới"""
    obj = await create_cam_bien(db, current_user.ma_nguoi_dung, payload)
    await db.commit()
    return SensorOut(
        ma_cam_bien=_extract(obj, "ma_cam_bien"),
        ten_cam_bien=_extract(obj, "ten_cam_bien"),
        mo_ta=_extract(obj, "mo_ta"),
        ngay_lap_dat=_extract(obj, "ngay_lap_dat"),
        ma_may_bom=_extract(obj, "ma_may_bom"),
        loai=_extract(obj, "loai"),
        thoi_gian_tao=_extract(obj, "thoi_gian_tao"),
    )

@router.get("/", status_code=200)
async def list_cam_bien_endpoint(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách cảm biến."""
    rows = await list_cam_bien_for_user(db, current_user.ma_nguoi_dung, limit, offset)
    items = [
        SensorOut(
            ma_cam_bien=_extract(r, "ma_cam_bien"),
            ten_cam_bien=_extract(r, "ten_cam_bien"),
            mo_ta=_extract(r, "mo_ta"),
            ngay_lap_dat=_extract(r, "ngay_lap_dat"),
            thoi_gian_tao=_extract(r, "thoi_gian_tao"),
            ma_may_bom=_extract(r, "ma_may_bom"),
            ten_may_bom=_extract(r, "ten_may_bom"),
            trang_thai=_extract(r, "trang_thai"),
            loai=_extract(r, "loai"),
            ten_loai_cam_bien=_extract(r, "ten_loai_cam_bien"),
        )
        for r in rows
    ]
    return {"data": items, "limit": limit, "offset": offset, "total": len(items)}


@router.get("/{ma_cam_bien}", status_code=200)
async def get_cam_bien_endpoint(
    ma_cam_bien: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy thông tin cảm biến theo mã cảm biến."""
    row = await get_cam_bien_with_names_by_id(db, ma_cam_bien)
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảm biến")
    if str(row.get("ma_nguoi_dung")) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập dữ liệu người khác")

    return SensorOut(
        ma_cam_bien=_extract(row, "ma_cam_bien"),
        ten_cam_bien=_extract(row, "ten_cam_bien"),
        mo_ta=_extract(row, "mo_ta"),
        ngay_lap_dat=_extract(row, "ngay_lap_dat"),
        ma_may_bom=_extract(row, "ma_may_bom"),
        ten_may_bom=_extract(row, "ten_may_bom"),
        trang_thai=_extract(row, "trang_thai"),
        loai=_extract(row, "loai"),
        ten_loai_cam_bien=_extract(row, "ten_loai_cam_bien"),
        thoi_gian_tao=_extract(row, "thoi_gian_tao"),
    )


@router.put("/{ma_cam_bien}", status_code=200)
async def update_cam_bien_endpoint(
    ma_cam_bien: int,
    payload: SensorCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật thông tin cảm biến."""
    r = await get_cam_bien_by_id(db, ma_cam_bien)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảm biến")
    if str(r.get("ma_nguoi_dung") if hasattr(r, 'get') else getattr(r, 'ma_nguoi_dung', None)) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa cảm biến này")
    await update_cam_bien(db, ma_cam_bien, payload)
    await db.commit()
    return {"message": "Cập nhật cảm biến thành công", "ma_cam_bien": ma_cam_bien}


@router.delete("/{ma_cam_bien}", status_code=200)
async def delete_cam_bien_endpoint(
    ma_cam_bien: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá cảm biến theo mã cảm biến."""
    r = await get_cam_bien_by_id(db, ma_cam_bien)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảm biến")
    if str(r.get("ma_nguoi_dung") if hasattr(r, 'get') else getattr(r, 'ma_nguoi_dung', None)) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép xoá cảm biến này")

    await delete_cam_bien(db, ma_cam_bien)
    await db.commit()
    
    return {"message": "Xoá cảm biến thành công", "ma_cam_bien": ma_cam_bien}
