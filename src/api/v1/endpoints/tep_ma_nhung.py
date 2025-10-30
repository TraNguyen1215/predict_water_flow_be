import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.schemas.tep_ma_nhung import *
from src.crud.tep_ma_nhung import *

router = APIRouter()


def _to_schema(obj) -> TepMaNhungOut:
    return TepMaNhungOut(
        ma_tep_ma_nhung=getattr(obj, "ma_tep_ma_nhung", None),
        ten_tep=getattr(obj, "ten_tep", None),
        phien_ban=getattr(obj, "phien_ban", None),
        mo_ta=getattr(obj, "mo_ta", None),
        thoi_gian_tao=getattr(obj, "thoi_gian_tao", None),
        thoi_gian_cap_nhat=getattr(obj, "thoi_gian_cap_nhat", None),
    )


@router.get("/", status_code=200)
async def list_tep_ma_nhung_endpoint(
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách tệp mã nhúng"""

    if page is not None:
        offset = (page - 1) * limit

    rows, total = await list_tep_ma_nhung(db, limit=limit, offset=offset)
    data = [_to_schema(r) for r in rows]
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    return {
        "data": data,
        "limit": limit,
        "offset": offset,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    }


@router.get("/{ma_tep_ma_nhung}", status_code=200, response_model=TepMaNhungOut)
async def get_tep_ma_nhung_endpoint(
    ma_tep_ma_nhung: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Chi tiết tệp mã nhúng."""

    obj = await get_tep_ma_nhung_by_id(db, ma_tep_ma_nhung)
    if not obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp mã nhúng")
    return _to_schema(obj)


@router.post("/", status_code=201, response_model=TepMaNhungOut)
async def create_tep_ma_nhung_endpoint(
    payload: TepMaNhungCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Thêm tệp mã nhúng mới."""

    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới được phép thêm tệp mã nhúng")

    obj = await create_tep_ma_nhung(db, payload)
    await db.commit()
    await db.refresh(obj)
    return _to_schema(obj)


@router.put("/{ma_tep_ma_nhung}", status_code=200, response_model=TepMaNhungOut)
async def update_tep_ma_nhung_endpoint(
    ma_tep_ma_nhung: int,
    payload: TepMaNhungUpdate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật tệp mã nhúng."""

    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới được phép cập nhật tệp mã nhúng")

    obj = await update_tep_ma_nhung(db, ma_tep_ma_nhung, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp mã nhúng")
    await db.commit()
    await db.refresh(obj)
    return _to_schema(obj)


@router.delete("/{ma_tep_ma_nhung}", status_code=200)
async def delete_tep_ma_nhung_endpoint(
    ma_tep_ma_nhung: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá tệp mã nhúng."""

    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới được phép xoá tệp mã nhúng")

    deleted = await delete_tep_ma_nhung(db, ma_tep_ma_nhung)
    if not deleted:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp mã nhúng")
    await db.commit()
    return {
        "message": "Xoá tệp mã nhúng thành công",
        "ma_tep_ma_nhung": ma_tep_ma_nhung,
    }
