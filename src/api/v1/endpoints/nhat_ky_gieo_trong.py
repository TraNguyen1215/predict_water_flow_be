from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import math
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from src.api import deps
from src.schemas.nhat_ky_gieo_trong import NhatKyGieoTrongCreate, NhatKyGieoTrongOut
from src.crud.nhat_ky_gieo_trong import (
    create_nhat_ky_gieo_trong,
    list_nhat_ky_gieo_trong_for_user,
    list_nhat_ky_gieo_trong_by_date,
    get_nhat_ky_gieo_trong_by_id,
    update_nhat_ky_gieo_trong,
    delete_nhat_ky_gieo_trong,
)

router = APIRouter()


@router.post("/", status_code=201, response_model=NhatKyGieoTrongOut)
async def create_nhat_ky_gieo_trong_endpoint(
    payload: NhatKyGieoTrongCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo nhật ký gieo trồng cho người dùng hiện tại."""

    # set owner to current user for security
    payload.ma_nguoi_dung = getattr(current_user, 'ma_nguoi_dung', None)
    obj = await create_nhat_ky_gieo_trong(db, payload)
    await db.commit()
    await db.refresh(obj)
    return NhatKyGieoTrongOut(
        ma_gieo_trong=getattr(obj, 'ma_gieo_trong', None),
        ma_nguoi_dung=getattr(obj, 'ma_nguoi_dung', None),
        ten_cay_trong=getattr(obj, 'ten_cay_trong', None),
        noi_dung=getattr(obj, 'noi_dung', None),
        dien_tich_trong=getattr(obj, 'dien_tich_trong', None),
        ngay_gieo_trong=getattr(obj, 'ngay_gieo_trong', None),
        giai_doan=getattr(obj, 'giai_doan', None),
        thoi_gian_da_gieo=getattr(obj, 'thoi_gian_da_gieo', None),
        trang_thai=getattr(obj, 'trang_thai', None),
        thoi_gian_tao=getattr(obj, 'thoi_gian_tao', None),
        thoi_gian_cap_nhat=getattr(obj, 'thoi_gian_cap_nhat', None),
    )


@router.get("/", status_code=200)
async def list_nhat_ky_gieo_trong(
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách nhật ký gieo trồng của người dùng hiện tại (phân trang)."""
    if page is not None:
        offset = (page - 1) * limit

    rows, total = await list_nhat_ky_gieo_trong_for_user(db, current_user.ma_nguoi_dung, limit, offset)
    items = [
        NhatKyGieoTrongOut(
            ma_gieo_trong=r.ma_gieo_trong,
            ma_nguoi_dung=r.ma_nguoi_dung,
            ten_cay_trong=r.ten_cay_trong,
            noi_dung=r.noi_dung,
            dien_tich_trong=r.dien_tich_trong,
            ngay_gieo_trong=r.ngay_gieo_trong,
            giai_doan=r.giai_doan,
            thoi_gian_da_gieo=r.thoi_gian_da_gieo,
            trang_thai=r.trang_thai,
            thoi_gian_tao=r.thoi_gian_tao,
            thoi_gian_cap_nhat=r.thoi_gian_cap_nhat,
        )
        for r in rows
    ]
    page_num = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    return {"data": items, "limit": limit, "offset": offset, "page": page_num, "total_pages": total_pages, "total": total}


@router.get("/ngay/{ngay}", status_code=200)
async def list_nhat_ky_gieo_trong_theo_ngay(
    ngay: date,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy nhật ký gieo trồng theo ngày gieo cho người dùng hiện tại."""
    rows = await list_nhat_ky_gieo_trong_by_date(db, current_user.ma_nguoi_dung, ngay)
    items = [
        NhatKyGieoTrongOut(
            ma_gieo_trong=r.ma_gieo_trong,
            ma_nguoi_dung=r.ma_nguoi_dung,
            ten_cay_trong=r.ten_cay_trong,
            noi_dung=r.noi_dung,
            dien_tich_trong=r.dien_tich_trong,
            ngay_gieo_trong=r.ngay_gieo_trong,
            giai_doan=r.giai_doan,
            thoi_gian_da_gieo=r.thoi_gian_da_gieo,
            trang_thai=r.trang_thai,
            thoi_gian_tao=r.thoi_gian_tao,
            thoi_gian_cap_nhat=r.thoi_gian_cap_nhat,
        )
        for r in rows
    ]
    return {"data": items, "total": len(items)}


@router.get("/{ma_gieo_trong}", status_code=200, response_model=NhatKyGieoTrongOut)
async def get_nhat_ky_gieo_trong_endpoint(
    ma_gieo_trong: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy chi tiết nhật ký gieo trồng (chỉ chủ sở hữu)."""
    r = await get_nhat_ky_gieo_trong_by_id(db, ma_gieo_trong)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký gieo trồng")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập nhật ký của người khác")
    return NhatKyGieoTrongOut(
        ma_gieo_trong=r.ma_gieo_trong,
        ma_nguoi_dung=r.ma_nguoi_dung,
        ten_cay_trong=r.ten_cay_trong,
        noi_dung=r.noi_dung,
        dien_tich_trong=r.dien_tich_trong,
        ngay_gieo_trong=r.ngay_gieo_trong,
        giai_doan=r.giai_doan,
        thoi_gian_da_gieo=r.thoi_gian_da_gieo,
        trang_thai=r.trang_thai,
        thoi_gian_tao=r.thoi_gian_tao,
        thoi_gian_cap_nhat=r.thoi_gian_cap_nhat,
    )


@router.put("/{ma_gieo_trong}", status_code=200)
async def update_nhat_ky_gieo_trong_endpoint(
    ma_gieo_trong: int,
    payload: NhatKyGieoTrongCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật nhật ký gieo trồng (chỉ chủ sở hữu)."""
    r = await get_nhat_ky_gieo_trong_by_id(db, ma_gieo_trong)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký gieo trồng")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa nhật ký của người khác")

    obj = await update_nhat_ky_gieo_trong(db, ma_gieo_trong, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký gieo trồng")
    await db.commit()
    return {"message": "Cập nhật nhật ký gieo trồng thành công", "ma_gieo_trong": ma_gieo_trong}


@router.delete("/{ma_gieo_trong}", status_code=200)
async def delete_nhat_ky_gieo_trong_endpoint(
    ma_gieo_trong: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá nhật ký gieo trồng (chỉ chủ sở hữu)."""
    r = await get_nhat_ky_gieo_trong_by_id(db, ma_gieo_trong)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký gieo trồng")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép xoá nhật ký của người khác")

    await delete_nhat_ky_gieo_trong(db, ma_gieo_trong)
    await db.commit()
    return {"message": "Xoá nhật ký gieo trồng thành công", "ma_gieo_trong": ma_gieo_trong}
