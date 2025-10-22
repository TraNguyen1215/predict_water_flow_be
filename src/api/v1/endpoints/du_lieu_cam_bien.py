from datetime import date
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.schemas.data import DataOut, DataCreate
from src.crud.du_lieu_cam_bien import list_du_lieu_for_user, list_du_lieu_by_day, get_du_lieu_by_id, update_du_lieu
from src.crud.may_bom import get_may_bom_by_id

router = APIRouter()


@router.get("/", status_code=200)
async def list_du_lieu(
    ma_may_bom: Optional[int] = Query(None),
    limit: int = Query(15, ge=1, le=1000),
    offset: int = Query(0, ge=0),
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

    rows, total = await list_du_lieu_for_user(db, current_user.ma_nguoi_dung, ma_may_bom, limit, offset)
    items = [
        DataOut(
            ma_du_lieu=str(r.ma_du_lieu) if isinstance(r.ma_du_lieu, uuid.UUID) else r.ma_du_lieu,
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
            ghi_chu=r.ghi_chu,
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
    limit: int = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
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
                ma_du_lieu=str(r.ma_du_lieu) if isinstance(r.ma_du_lieu, uuid.UUID) else r.ma_du_lieu,
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
                ghi_chu=r.ghi_chu,
            )
            for r in rows
        ]
        return {"data": items, "total": len(items)}
    else:
        rows, total = await list_du_lieu_for_user(db, current_user.ma_nguoi_dung, ma_may_bom, limit, offset)
        items = [
            DataOut(
                ma_du_lieu=str(r.ma_du_lieu) if isinstance(r.ma_du_lieu, uuid.UUID) else r.ma_du_lieu,
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
                ghi_chu=r.ghi_chu,
            )
            for r in rows
        ]
        page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = math.ceil(total / limit) if limit > 0 else 1
        return {"data": items, "limit": limit, "offset": offset, "page": page, "total_pages": total_pages, "total": total}


@router.put("/{ma_du_lieu}", status_code=200)
async def update_du_lieu(
    ma_du_lieu: uuid.UUID,
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
    if getattr(payload, "ghi_chu", None) is not None:
        updates["ghi_chu"] = payload.ghi_chu

    if not updates:
        return {"message": "Không có trường nào để cập nhật"}

    await update_du_lieu(db, ma_du_lieu, updates)
    await db.commit()
    return {"message": "Cập nhật dữ liệu thành công", "ma_du_lieu": ma_du_lieu}
