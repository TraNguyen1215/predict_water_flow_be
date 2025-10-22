from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.schemas.nhat_ky import NhatKyCreate, NhatKyOut
from src.crud.nhat_ky_may_bom import create_nhat_ky, list_nhat_ky_for_pump, get_nhat_ky_by_id, update_nhat_ky, delete_nhat_ky
from src.crud.may_bom import get_may_bom_by_id

router = APIRouter()


@router.post("/nhat-ky-may-bom", status_code=201, response_model=NhatKyOut)
async def create_nhat_ky(
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

    ma = await create_nhat_ky(db, payload)
    await db.commit()
    return NhatKyOut(ma_nhat_ky=ma, ma_may_bom=payload.ma_may_bom, thoi_gian_bat=payload.thoi_gian_bat, thoi_gian_tat=payload.thoi_gian_tat, ghi_chu=payload.ghi_chu)


@router.get("/nhat-ky-may-bom", status_code=200)
async def list_nhat_ky(
    ma_may_bom: int = Query(...),
    limit: int = Query(50, ge=1, le=500),
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

    rows = await list_nhat_ky_for_pump(db, ma_may_bom, limit, offset)
    items = [
        NhatKyOut(ma_nhat_ky=r.ma_nhat_ky, ma_may_bom=r.ma_may_bom, thoi_gian_bat=r.thoi_gian_bat, thoi_gian_tat=r.thoi_gian_tat, ghi_chu=r.ghi_chu, thoi_gian_tao=r.thoi_gian_tao)
        for r in rows
    ]

    return {"data": items, "limit": limit, "offset": offset, "total": len(items)}


@router.get("/nhat-ky-may-bom/{ma_nhat_ky}", status_code=200)
async def get_nhat_ky(
    ma_nhat_ky: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy thông tin nhật ký theo mã nhật ký (chỉ chủ sở hữu)."""
    
    r = await get_nhat_ky_by_id(db, ma_nhat_ky)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập nhật ký của người khác")
    
    return NhatKyOut(ma_nhat_ky=r.ma_nhat_ky, ma_may_bom=r.ma_may_bom, thoi_gian_bat=r.thoi_gian_bat, thoi_gian_tat=r.thoi_gian_tat, ghi_chu=r.ghi_chu, thoi_gian_tao=r.thoi_gian_tao)


@router.put("/nhat-ky-may-bom/{ma_nhat_ky}", status_code=200)
async def update_nhat_ky(
    ma_nhat_ky: int,
    payload: NhatKyCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật nhật ký (chỉ chủ sở hữu)."""
    
    r = await get_nhat_ky_by_id(db, ma_nhat_ky)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa nhật ký của người khác")

    await update_nhat_ky(db, ma_nhat_ky, payload)
    await db.commit()
    
    return {"message": "Cập nhật nhật ký thành công", "ma_nhat_ky": ma_nhat_ky}


@router.delete("/nhat-ky-may-bom/{ma_nhat_ky}", status_code=200)
async def delete_nhat_ky(
    ma_nhat_ky: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá nhật ký (chỉ chủ sở hữu)."""
    
    r = await get_nhat_ky_by_id(db, ma_nhat_ky)
    
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép xoá nhật ký của người khác")

    await delete_nhat_ky(db, ma_nhat_ky)
    await db.commit()
    
    return {"message": "Xoá nhật ký thành công", "ma_nhat_ky": ma_nhat_ky}
