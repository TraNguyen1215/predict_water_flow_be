import datetime
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pathlib import Path
import shutil
from src.api import deps
from src.schemas.loai_cam_bien import LoaiCamBienCreate, LoaiCamBienOut
from src.crud.loai_cam_bien import list_loai_cam_bien, get_loai_cam_bien_by_id, create_loai_cam_bien, update_loai_cam_bien, delete_loai_cam_bien

router = APIRouter()

# Lấy thông tin loại cảm biến
@router.get("/", status_code=200)
async def get_loai_cam_bien(
    limit: int = Query(15, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Lấy danh sách loại cảm biến.

    """

    if page is not None:
        offset = (page - 1) * limit

    rows, total = await list_loai_cam_bien(db, limit=limit, offset=offset)
    data = [LoaiCamBienOut(ma_loai_cam_bien=row.ma_loai_cam_bien, ten_loai_cam_bien=row.ten_loai_cam_bien, thoi_gian_tao=row.thoi_gian_tao, thoi_gian_cap_nhat=row.thoi_gian_cap_nhat) for row in rows]
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    return {"data": data, "limit": limit, "offset": offset, "page": page, "total_pages": total_pages, "total": total}


# Lấy thông tin loại cảm biến theo mã
@router.get("/{ma_loai_cam_bien}", status_code=200, response_model=LoaiCamBienOut)
async def get_loai_cam_bien_theo_ma(
    ma_loai_cam_bien: int,
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Lấy thông tin loại cảm biến theo mã loại cảm biến.
    """
    
    r = await get_loai_cam_bien_by_id(db, ma_loai_cam_bien)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy loại cảm biến")
    return LoaiCamBienOut(ma_loai_cam_bien=r.ma_loai_cam_bien, ten_loai_cam_bien=r.ten_loai_cam_bien, thoi_gian_tao=r.thoi_gian_tao, thoi_gian_cap_nhat=r.thoi_gian_cap_nhat)

# Thêm loại cảm biến mới
@router.post("/", status_code=201)
async def create_loai_cam_bien_endpoint(
    payload: LoaiCamBienCreate,
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Thêm loại cảm biến mới.
    """

    await create_loai_cam_bien(db, payload)
    await db.commit()
    return {"message": "Thêm loại cảm biến thành công", "ten_loai_cam_bien": payload.ten_loai_cam_bien}

# Cập nhật loại cảm biến
@router.put("/{ma_loai_cam_bien}", status_code=200)
async def update_loai_cam_bien_endpoint(
    ma_loai_cam_bien: int,
    payload: LoaiCamBienCreate,
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Cập nhật loại cảm biến theo mã loại cảm biến.
    """

    r = await get_loai_cam_bien_by_id(db, ma_loai_cam_bien)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy loại cảm biến")

    await update_loai_cam_bien(db, ma_loai_cam_bien, payload)
    await db.commit()
    return {
        "message": "Cập nhật loại cảm biến thành công!",
        "ma_loai_cam_bien": ma_loai_cam_bien,
    }

# Xoá loại cảm biến
@router.delete("/{ma_loai_cam_bien}", status_code=200)
async def delete_loai_cam_bien_endpoint(
    ma_loai_cam_bien: int,
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Xoá loại cảm biến theo mã loại cảm biến.
    """

    r = await get_loai_cam_bien_by_id(db, ma_loai_cam_bien)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy loại cảm biến")

    await delete_loai_cam_bien(db, ma_loai_cam_bien)
    await db.commit()
    return {
        "message": "Xoá loại cảm biến thành công!",
        "ma_loai_cam_bien": ma_loai_cam_bien,
    }