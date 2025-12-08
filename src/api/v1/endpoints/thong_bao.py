from typing import Optional
import math
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.schemas.thong_bao import ThongBaoCreate, ThongBaoUpdate, ThongBaoResponse
from src.crud import thong_bao as crud_thong_bao

router = APIRouter()


@router.post("/", status_code=201, response_model=ThongBaoResponse)
async def create_thong_bao(
    payload: ThongBaoCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo thông báo mới"""
    thong_bao = await crud_thong_bao.create(db, payload)
    return thong_bao


@router.get("/", status_code=200)
async def get_thong_bao_list(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy danh sách thông báo của người dùng"""
    if page is not None:
        offset = (page - 1) * limit

    thong_baos, total = await crud_thong_bao.get_by_user(
        db, current_user.ma_nguoi_dung, skip=offset, limit=limit
    )
    
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    
    return {
        "data": thong_baos,
        "limit": limit,
        "offset": offset,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    }


@router.get("/unread", status_code=200)
async def get_unread_thong_bao(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy danh sách thông báo chưa xem"""
    if page is not None:
        offset = (page - 1) * limit

    thong_baos, total = await crud_thong_bao.get_unread_by_user(
        db, current_user.ma_nguoi_dung, skip=offset, limit=limit
    )
    
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    
    return {
        "data": thong_baos,
        "limit": limit,
        "offset": offset,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    }


@router.get("/count-unread", status_code=200)
async def count_unread_thong_bao(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Đếm số thông báo chưa xem"""
    count = await crud_thong_bao.count_unread_by_user(db, current_user.ma_nguoi_dung)
    return {"count": count}


@router.get("/{ma_thong_bao}", status_code=200, response_model=ThongBaoResponse)
async def get_thong_bao_detail(
    ma_thong_bao: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy chi tiết thông báo"""
    thong_bao = await crud_thong_bao.get_by_id(db, ma_thong_bao)
    if not thong_bao:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")

    if thong_bao.ma_nguoi_dung != current_user.ma_nguoi_dung:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem thông báo này")

    return thong_bao


@router.put("/{ma_thong_bao}", status_code=200, response_model=ThongBaoResponse)
async def update_thong_bao(
    ma_thong_bao: int,
    payload: ThongBaoUpdate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật thông báo"""
    thong_bao = await crud_thong_bao.get_by_id(db, ma_thong_bao)
    if not thong_bao:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")

    if thong_bao.ma_nguoi_dung != current_user.ma_nguoi_dung:
        raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật thông báo này")

    updated = await crud_thong_bao.update(db, ma_thong_bao, payload)
    return updated


@router.post("/{ma_thong_bao}/mark-as-read", status_code=200, response_model=ThongBaoResponse)
async def mark_as_read(
    ma_thong_bao: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Đánh dấu thông báo đã xem"""
    thong_bao = await crud_thong_bao.get_by_id(db, ma_thong_bao)
    if not thong_bao:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")

    if thong_bao.ma_nguoi_dung != current_user.ma_nguoi_dung:
        raise HTTPException(status_code=403, detail="Bạn không có quyền đánh dấu thông báo này")

    updated = await crud_thong_bao.mark_as_read(db, ma_thong_bao)
    return updated


@router.post("/mark-all-as-read", status_code=200)
async def mark_all_as_read(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Đánh dấu tất cả thông báo đã xem"""
    count = await crud_thong_bao.mark_all_as_read(db, current_user.ma_nguoi_dung)
    return {"count": count}


@router.delete("/{ma_thong_bao}", status_code=200)
async def delete_thong_bao(
    ma_thong_bao: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá thông báo"""
    thong_bao = await crud_thong_bao.get_by_id(db, ma_thong_bao)
    if not thong_bao:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")

    if thong_bao.ma_nguoi_dung != current_user.ma_nguoi_dung:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xoá thông báo này")

    success = await crud_thong_bao.delete(db, ma_thong_bao)
    return {"deleted": success}
