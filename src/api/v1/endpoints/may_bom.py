from typing import Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.schemas.pump import PumpCreate, PumpOut
from src.crud.may_bom import create_may_bom, list_may_bom_for_user, get_may_bom_by_id, update_may_bom, delete_may_bom

router = APIRouter()


@router.post("/", status_code=201, response_model=PumpOut)
async def create_may_bom(
    payload: PumpCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo máy bơm mới"""
    ma = await create_may_bom(db, current_user.ma_nguoi_dung, payload)
    await db.commit()
    return PumpOut(
        ma_may_bom=ma,
        ten_may_bom=payload.ten_may_bom,
        mo_ta=payload.mo_ta,
        ma_iot_lk=payload.ma_iot_lk,
        che_do=payload.che_do,
        trang_thai=payload.trang_thai,
    )


@router.get("/", status_code=200)
async def list_may_bom(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách máy bơm"""
    rows = await list_may_bom_for_user(db, current_user.ma_nguoi_dung, limit, offset)
    items = [
        PumpOut(
            ma_may_bom=r.ma_may_bom,
            ten_may_bom=r.ten_may_bom,
            mo_ta=r.mo_ta,
            ma_iot_lk=r.ma_iot_lk,
            che_do=r.che_do,
            trang_thai=r.trang_thai,
            thoi_gian_tao=r.thoi_gian_tao,
        )
        for r in rows
    ]
    return {"data": items, "limit": limit, "offset": offset, "total": len(items)}


@router.get("/{ma_may_bom}", status_code=200)
async def get_may_bom(
    ma_may_bom: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy thông tin máy bơm theo mã máy bơm (chỉ chủ sở hữu mới được phép truy cập)."""
    r = await get_may_bom_by_id(db, ma_may_bom)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập dữ liệu người khác")
    return PumpOut(
        ma_may_bom=r.ma_may_bom,
        ten_may_bom=r.ten_may_bom,
        mo_ta=r.mo_ta,
        ma_iot_lk=r.ma_iot_lk,
        che_do=r.che_do,
        trang_thai=r.trang_thai,
    )


@router.put("/{ma_may_bom}", status_code=200)
async def update_may_bom(
    ma_may_bom: int,
    payload: PumpCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật thông tin máy bơm (chỉ chủ sở hữu mới được phép chỉnh sửa)."""
    r = await get_may_bom_by_id(db, ma_may_bom)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa máy bơm này")

    await update_may_bom(db, ma_may_bom, payload)
    await db.commit()
    return {"message": "Cập nhật máy bơm thành công", "ma_may_bom": ma_may_bom}


@router.delete("/{ma_may_bom}", status_code=200)
async def delete_may_bom(
    ma_may_bom: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá máy bơm (chỉ chủ sở hữu mới được phép xoá)."""
    r = await get_may_bom_by_id(db, ma_may_bom)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép xoá máy bơm này")

    await delete_may_bom(db, ma_may_bom)
    await db.commit()
    return {"message": "Xoá máy bơm thành công", "ma_may_bom": ma_may_bom}
