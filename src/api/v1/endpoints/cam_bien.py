from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from src.api import deps
from src.schemas.sensor import SensorCreate, SensorOut

router = APIRouter()


@router.post("/", status_code=201, response_model=SensorOut)
async def create_cam_bien(
    payload: SensorCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo cảm biến mới"""
    result = await db.execute(
        text(
            "INSERT INTO cam_bien(ma_nguoi_dung, ten_cam_bien, mo_ta, ngay_lap_dat, ma_may_bom, thoi_gian_tao, loai) VALUES(:ma_nd, :ten, :mo, :ngay, :may, NOW(), :loai) RETURNING ma_cam_bien"
        ),
        {
            "ma_nd": str(current_user.ma_nguoi_dung),
            "ten": payload.ten_cam_bien,
            "mo": payload.mo_ta,
            "ngay": payload.ngay_lap_dat,
            "may": payload.ma_may_bom,
            "loai": payload.loai,
        },
    )
    inserted = result.fetchone()
    await db.commit()
    ma = inserted.ma_cam_bien if inserted else None
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
    result = await db.execute(
        text(
            "SELECT c.*, m.ten_may_bom, l.ten_loai_cam_bien FROM cam_bien c LEFT JOIN may_bom m ON c.ma_may_bom = m.ma_may_bom LEFT JOIN loai_cam_bien l ON c.loai = l.ma_loai_cam_bien WHERE c.ma_nguoi_dung = :ma_nd ORDER BY c.thoi_gian_tao DESC LIMIT :lim OFFSET :off"
        ),
        {"ma_nd": str(current_user.ma_nguoi_dung), "lim": limit, "off": offset},
    )
    
    rows = result.fetchall()
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
    result = await db.execute(
        text("SELECT c.*, m.ten_may_bom, l.ten_loai_cam_bien FROM cam_bien c LEFT JOIN may_bom m ON c.ma_may_bom = m.ma_may_bom LEFT JOIN loai_cam_bien l ON c.loai = l.ma_loai_cam_bien WHERE c.ma_cam_bien = :ma"),
        {"ma": ma_cam_bien},
    )
    r = result.fetchone()
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
    result = await db.execute(text("SELECT ma_nguoi_dung FROM cam_bien WHERE ma_cam_bien = :ma"), {"ma": ma_cam_bien})
    r = result.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảm biến")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa cảm biến này")

    await db.execute(
        text(
            "UPDATE cam_bien SET ten_cam_bien = :ten, mo_ta = :mo, ma_may_bom = :may, ngay_lap_dat = :ngay, trang_thai = :tt, loai = :loai, thoi_gian_cap_nhat = NOW() WHERE ma_cam_bien = :ma"
        ),
        {"ten": payload.ten_cam_bien, "mo": payload.mo_ta, "may": payload.ma_may_bom, "ngay": payload.ngay_lap_dat, "tt": payload.trang_thai if hasattr(payload, 'trang_thai') else None, "loai": payload.loai, "ma": ma_cam_bien},
    )
    await db.commit()
    return {"message": "Cập nhật cảm biến thành công", "ma_cam_bien": ma_cam_bien}


@router.delete("/{ma_cam_bien}", status_code=200)
async def delete_cam_bien(
    ma_cam_bien: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá cảm biến theo mã cảm biến."""
    result = await db.execute(text("SELECT ma_nguoi_dung FROM cam_bien WHERE ma_cam_bien = :ma"), {"ma": ma_cam_bien})
    r = result.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảm biến")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép xoá cảm biến này")

    await db.execute(text("DELETE FROM cam_bien WHERE ma_cam_bien = :ma"), {"ma": ma_cam_bien})
    await db.commit()
    
    return {"message": "Xoá cảm biến thành công", "ma_cam_bien": ma_cam_bien}
