from typing import Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.schemas.pump import PumpCreate, PumpOut

router = APIRouter()


@router.post("/", status_code=201, response_model=PumpOut)
async def create_may_bom(
    payload: PumpCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo máy bơm mới"""
    result = await db.execute(
        text(
            "INSERT INTO may_bom(ten_may_bom, mo_ta, ma_iot_lk, che_do, trang_thai, ma_nguoi_dung, thoi_gian_tao) VALUES(:ten, :mo, :iot, :che, :tt, :ma_nd, NOW()) RETURNING ma_may_bom"
        ),
        {
            "ten": payload.ten_may_bom,
            "mo": payload.mo_ta,
            "iot": payload.ma_iot_lk,
            "che": payload.che_do,
            "tt": payload.trang_thai,
            "ma_nd": str(current_user.ma_nguoi_dung),
        },
    )
    inserted = result.fetchone()
    await db.commit()
    ma = inserted.ma_may_bom if inserted else None
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
    result = await db.execute(
        text(
            "SELECT * FROM may_bom WHERE ma_nguoi_dung = :ma_nd ORDER BY thoi_gian_tao DESC LIMIT :lim OFFSET :off"
        ),
        {"ma_nd": str(current_user.ma_nguoi_dung), "lim": limit, "off": offset},
    )
    rows = result.fetchall()
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
    result = await db.execute(text("SELECT * FROM may_bom WHERE ma_may_bom = :ma"), {"ma": ma_may_bom})
    r = result.fetchone()
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
    result = await db.execute(text("SELECT ma_nguoi_dung FROM may_bom WHERE ma_may_bom = :ma"), {"ma": ma_may_bom})
    r = result.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa máy bơm này")

    await db.execute(
        text(
            "UPDATE may_bom SET ten_may_bom = :ten, mo_ta = :mo, ma_iot_lk = :iot, che_do = :che, trang_thai = :tt, thoi_gian_cap_nhat = NOW() WHERE ma_may_bom = :ma"
        ),
        {"ten": payload.ten_may_bom, "mo": payload.mo_ta, "iot": payload.ma_iot_lk, "che": payload.che_do, "tt": payload.trang_thai, "ma": ma_may_bom},
    )
    await db.commit()
    return {"message": "Cập nhật máy bơm thành công", "ma_may_bom": ma_may_bom}


@router.delete("/{ma_may_bom}", status_code=200)
async def delete_may_bom(
    ma_may_bom: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá máy bơm (chỉ chủ sở hữu mới được phép xoá)."""
    result = await db.execute(text("SELECT ma_nguoi_dung FROM may_bom WHERE ma_may_bom = :ma"), {"ma": ma_may_bom})
    r = result.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép xoá máy bơm này")

    await db.execute(text("DELETE FROM may_bom WHERE ma_may_bom = :ma"), {"ma": ma_may_bom})
    await db.commit()
    return {"message": "Xoá máy bơm thành công", "ma_may_bom": ma_may_bom}
