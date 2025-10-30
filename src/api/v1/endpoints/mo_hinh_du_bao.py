import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.schemas.mo_hinh_du_bao import (
    MoHinhDuBaoCreate,
    MoHinhDuBaoOut,
    MoHinhDuBaoUpdate,
)
from src.crud.mo_hinh_du_bao import (
    create_mo_hinh_du_bao,
    delete_mo_hinh_du_bao,
    get_mo_hinh_du_bao_by_id,
    list_mo_hinh_du_bao,
    update_mo_hinh_du_bao,
)

router = APIRouter()


def _to_schema(obj) -> MoHinhDuBaoOut:
    return MoHinhDuBaoOut(
        ma_mo_hinh=getattr(obj, "ma_mo_hinh", None),
        ten_mo_hinh=getattr(obj, "ten_mo_hinh", None),
        phien_ban=getattr(obj, "phien_ban", None),
        thoi_gian_tao=getattr(obj, "thoi_gian_tao", None),
        thoi_gian_cap_nhat=getattr(obj, "thoi_gian_cap_nhat", None),
        trang_thai=getattr(obj, "trang_thai", None),
    )


@router.get("/", status_code=200)
async def list_mo_hinh_du_bao_endpoint(
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách mô hình dự báo."""

    if page is not None:
        offset = (page - 1) * limit

    rows, total = await list_mo_hinh_du_bao(db, limit=limit, offset=offset)
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


@router.get("/{ma_mo_hinh}", status_code=200, response_model=MoHinhDuBaoOut)
async def get_mo_hinh_du_bao_endpoint(
    ma_mo_hinh: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Chi tiết mô hình dự báo."""

    obj = await get_mo_hinh_du_bao_by_id(db, ma_mo_hinh)
    if not obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy mô hình dự báo")
    return _to_schema(obj)


@router.post("/", status_code=201, response_model=MoHinhDuBaoOut)
async def create_mo_hinh_du_bao_endpoint(
    payload: MoHinhDuBaoCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Thêm mô hình dự báo mới."""

    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới được phép thêm mô hình dự báo")

    obj = await create_mo_hinh_du_bao(db, payload)
    await db.commit()
    await db.refresh(obj)
    return _to_schema(obj)


@router.put("/{ma_mo_hinh}", status_code=200, response_model=MoHinhDuBaoOut)
async def update_mo_hinh_du_bao_endpoint(
    ma_mo_hinh: int,
    payload: MoHinhDuBaoUpdate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật mô hình dự báo."""

    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới được phép cập nhật mô hình dự báo")

    obj = await update_mo_hinh_du_bao(db, ma_mo_hinh, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy mô hình dự báo")
    await db.commit()
    await db.refresh(obj)
    return _to_schema(obj)


@router.delete("/{ma_mo_hinh}", status_code=200)
async def delete_mo_hinh_du_bao_endpoint(
    ma_mo_hinh: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá mô hình dự báo."""

    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới được phép xoá mô hình dự báo")

    deleted = await delete_mo_hinh_du_bao(db, ma_mo_hinh)
    if not deleted:
        raise HTTPException(status_code=404, detail="Không tìm thấy mô hình dự báo")
    await db.commit()
    return {
        "message": "Xoá mô hình dự báo thành công",
        "ma_mo_hinh": ma_mo_hinh,
    }
