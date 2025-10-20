from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from src.api import deps

router = APIRouter()


@router.post("/", status_code=201)
async def create_cam_bien(
    ten_cam_bien: str = Body(..., embed=True),
    mo_ta: Optional[str] = Body(None, embed=True),
    ma_may_bom: int = Body(None, embed=True),
    ngay_lap_dat: Optional[date] = Body(None, embed=True),
    loai: int = Body(..., embed=True),
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
            "ten": ten_cam_bien,
            "mo": mo_ta,
            "ngay": ngay_lap_dat,
            "may": ma_may_bom,
            "loai": loai
        },
    )
    inserted = result.fetchone()
    await db.commit()
    ma = inserted.ma_cam_bien if inserted else None
    return {"ma_cam_bien": ma, "ten_cam_bien": ten_cam_bien, "mo_ta": mo_ta, "ma_may_bom": ma_may_bom, "ngay_lap_dat": ngay_lap_dat, "loai": loai}


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
        {
            "ma_cam_bien": r.ma_cam_bien,
            "ten_cam_bien": r.ten_cam_bien,
            "mo_ta": r.mo_ta,
            "ngay_lap_dat": r.ngay_lap_dat,
            "thoi_gian_tao": r.thoi_gian_tao,
            "ma_may_bom": r.ma_may_bom,
            "ten_may_bom": r.ten_may_bom,
            "trang_thai": r.trang_thai,
            "loai": r.loai,
            "ten_loai_cam_bien": r.ten_loai_cam_bien,
        }
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
    
    return {
        "ma_cam_bien": r.ma_cam_bien,
        "ten_cam_bien": r.ten_cam_bien,
        "mo_ta": r.mo_ta,
        "ngay_lap_dat": r.ngay_lap_dat,
        "ma_may_bom": r.ma_may_bom,
        "ten_may_bom": r.ten_may_bom,
        "trang_thai": r.trang_thai,
        "loai": r.loai,
        "ten_loai_cam_bien": r.ten_loai_cam_bien,
    }


@router.put("/{ma_cam_bien}", status_code=200)
async def update_cam_bien(
    ma_cam_bien: int,
    ten_cam_bien: str = Body(..., embed=True),
    mo_ta: Optional[str] = Body(None, embed=True),
    ma_may_bom: int = Body(None, embed=True),
    ngay_lap_dat: Optional[date] = Body(None, embed=True),
    trang_thai: Optional[bool] = Body(None, embed=True),
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
            "UPDATE cam_bien SET ten_cam_bien = :ten, mo_ta = :mo, ma_may_bom = :may, ngay_lap_dat = :ngay, trang_thai = :tt, thoi_gian_cap_nhat = NOW() WHERE ma_cam_bien = :ma"
        ),
        {"ten": ten_cam_bien, "mo": mo_ta, "may": ma_may_bom, "ngay": ngay_lap_dat, "tt": trang_thai, "ma": ma_cam_bien},
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
