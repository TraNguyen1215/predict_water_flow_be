from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.schemas.nhat_ky import NhatKyCreate, NhatKyOut
from src.crud.nhat_ky_may_bom import create_nhat_ky, list_nhat_ky_for_pump, get_nhat_ky_by_id, update_nhat_ky, delete_nhat_ky
from src.crud.may_bom import get_may_bom_by_id

router = APIRouter()


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
    return NhatKyOut(
        ma_nhat_ky=getattr(obj, "ma_nhat_ky"), # getattr(obj, "ma_nhat_ky", None),: là để tránh lỗi nếu obj không có thuộc tính ma_nhat_ky
        ma_may_bom=getattr(obj, "ma_may_bom", None),
        thoi_gian_bat=getattr(obj, "thoi_gian_bat", None),
        thoi_gian_tat=getattr(obj, "thoi_gian_tat", None),
        ghi_chu=getattr(obj, "ghi_chu", None),
        thoi_gian_tao=getattr(obj, "thoi_gian_tao"),
    )


@router.get("/", status_code=200)
async def list_nhat_ky_endpoint(
    ma_may_bom: int = Query(...),
    limit: int = Query(15, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách nhật ký cho một máy bơm (chỉ chủ sở hữu)."""
    
    pump = await get_may_bom_by_id(db, ma_may_bom)
    if not pump:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập nhật ký của máy bơm này")

    rows, total = await list_nhat_ky_for_pump(db, ma_may_bom, limit, offset)
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
