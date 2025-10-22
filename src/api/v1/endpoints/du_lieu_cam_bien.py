from datetime import date
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.schemas.data import DataOut, DataCreate

router = APIRouter()


@router.get("/", status_code=200)
async def list_du_lieu(
    ma_may_bom: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách dữ liệu cảm biến cho các máy bơm của người dùng đã xác thực. Tùy chọn lọc theo `ma_may_bom`."""
    if ma_may_bom:
        r = await db.execute(text("SELECT ma_nguoi_dung FROM may_bom WHERE ma_may_bom = :ma"), {"ma": ma_may_bom})
        pump = r.fetchone()
        if not pump:
            raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
        if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
            raise HTTPException(status_code=403, detail="Không được phép truy cập dữ liệu của máy bơm này")

    sql = "SELECT d.ma_du_lieu, d.ma_may_bom, d.ma_nguoi_dung, d.ngay, d.luu_luong_nuoc, d.do_am_dat, d.nhiet_do, d.do_am, d.mua, d.so_xung, d.tong_the_tich, d.thoi_gian_tao, d.ghi_chu FROM du_lieu_cam_bien d JOIN may_bom m ON d.ma_may_bom = m.ma_may_bom WHERE m.ma_nguoi_dung = :ma_nd"
    params = {"ma_nd": str(current_user.ma_nguoi_dung)}
    if ma_may_bom:
        sql += " AND d.ma_may_bom = :may"
        params["may"] = ma_may_bom
    sql += " ORDER BY d.thoi_gian_tao DESC LIMIT :lim OFFSET :off"
    params.update({"lim": limit, "off": offset})

    result = await db.execute(text(sql), params)
    rows = result.fetchall()
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
    return {"data": items, "limit": limit, "offset": offset, "total": len(items)}

@router.get("/ngay/{ngay}", status_code=200)
async def get_du_lieu_theo_ngay(
    ngay: date,
    ma_may_bom: int = Query(None),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy dữ liệu cảm biến theo ngày cho tất cả các máy bơm của người dùng đã xác thực."""
    sql = "SELECT d.ma_du_lieu, d.ma_may_bom, d.ma_nguoi_dung, d.ngay, d.luu_luong_nuoc, d.do_am_dat, d.nhiet_do, d.do_am, d.mua, d.so_xung, d.tong_the_tich, d.thoi_gian_tao, d.ghi_chu FROM du_lieu_cam_bien d JOIN may_bom m ON d.ma_may_bom = m.ma_may_bom WHERE m.ma_nguoi_dung = :ma_nd AND d.ngay = :ngay"
    params = {"ma_nd": str(current_user.ma_nguoi_dung), "ngay": ngay}
    
    if ma_may_bom:
        sql += " AND d.ma_may_bom = :may"
        params["may"] = ma_may_bom

    sql += " ORDER BY d.thoi_gian_tao DESC"
    
    result = await db.execute(text(sql), params)
    rows = result.fetchall()

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


@router.put("/{ma_du_lieu}", status_code=200)
async def update_du_lieu(
    ma_du_lieu: uuid.UUID,
    payload: DataCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật dữ liệu cảm biến theo mã dữ liệu cảm biến."""
    
    result = await db.execute(
        text(
            "SELECT d.ma_du_lieu, d.ma_may_bom, m.ma_nguoi_dung FROM du_lieu_cam_bien d JOIN may_bom m ON d.ma_may_bom = m.ma_may_bom WHERE d.ma_du_lieu = :ma"
        ),
        {"ma": str(ma_du_lieu)},
    )
    r = result.fetchone()
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

    set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
    sql = f"UPDATE du_lieu_cam_bien SET {set_clause}, thoi_gian_cap_nhat = NOW() WHERE ma_du_lieu = :ma"
    params = {**updates, "ma": str(ma_du_lieu)}
    await db.execute(text(sql), params)
    await db.commit()
    return {"message": "Cập nhật dữ liệu thành công", "ma_du_lieu": ma_du_lieu}
