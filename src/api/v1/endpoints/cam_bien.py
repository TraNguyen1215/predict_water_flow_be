from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from src.api import deps
from src.schemas.sensor import SensorCreate, SensorOut, SensorUpdate
from src.crud.cam_bien import *
from src.models.cam_bien import CamBien


def _extract(row, key):
    try:
        if hasattr(row, "get"):
            val = row.get(key)
        else:
            val = getattr(row, key)
    except Exception:
        try:
            val = row[key]
        except Exception:
            val = None

    if isinstance(val, CamBien):
        return getattr(val, "ma_cam_bien", None)
    return val

router = APIRouter()


@router.post("/", status_code=201, response_model=SensorOut)
async def create_cam_bien_endpoint(
    payload: SensorCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo cảm biến mới"""
    # Xác định người dùng mục tiêu (nếu là admin có thể tạo cho người khác)
    if current_user.quan_tri_vien:
        target_user_id = payload.ma_nguoi_dung
    else:
        target_user_id = current_user.ma_nguoi_dung

    # Kiểm tra xem người dùng đã có 4 cảm biến chưa
    if target_user_id:
        sensor_count = await count_cam_bien_for_user(db, target_user_id)
        if sensor_count >= 4:
            raise HTTPException(status_code=400, detail="Mỗi tài khoản chỉ được có tối đa 4 cảm biến. Xoá cảm biến cũ trước khi tạo cảm biến mới")
    
    obj = await create_cam_bien(db, target_user_id, payload)
    await db.commit()
    return SensorOut(
        ma_cam_bien=_extract(obj, "ma_cam_bien"),
        ten_cam_bien=_extract(obj, "ten_cam_bien"),
        mo_ta=_extract(obj, "mo_ta"),
        ngay_lap_dat=_extract(obj, "ngay_lap_dat"),
        ma_may_bom=_extract(obj, "ma_may_bom"),
        loai=_extract(obj, "loai"),
        thoi_gian_tao=_extract(obj, "thoi_gian_tao"),
    )

@router.get("/", status_code=200)
async def list_cam_bien_endpoint(
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách cảm biến (admin có thể xem tất cả, user chỉ xem của mình)."""
    if page is not None:
        offset = (page - 1) * limit

    # Admin xem tất cả, user chỉ xem của mình
    if current_user.quan_tri_vien:
        from src.crud.cam_bien import list_all_cam_bien
        rows, total = await list_all_cam_bien(db, limit, offset)
    else:
        rows, total = await list_cam_bien_for_user(db, current_user.ma_nguoi_dung, limit, offset)
    items = [
        SensorOut(
            ma_cam_bien=_extract(r, "ma_cam_bien"),
            ten_cam_bien=_extract(r, "ten_cam_bien"),
            mo_ta=_extract(r, "mo_ta"),
            ngay_lap_dat=_extract(r, "ngay_lap_dat"),
            thoi_gian_tao=_extract(r, "thoi_gian_tao"),
            ma_may_bom=_extract(r, "ma_may_bom"),
            ten_may_bom=_extract(r, "ten_may_bom"),
            trang_thai=_extract(r, "trang_thai"),
            loai=_extract(r, "loai"),
            ten_loai_cam_bien=_extract(r, "ten_loai_cam_bien"),
        )
        for r in rows
    ]
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    return {"data": items, "limit": limit, "offset": offset, "page": page, "total_pages": total_pages, "total": total}


@router.get("/{ma_cam_bien}", status_code=200)
async def get_cam_bien_endpoint(
    ma_cam_bien: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy thông tin cảm biến theo mã cảm biến (chủ sở hữu hoặc admin mới được phép truy cập)."""
    row = await get_cam_bien_with_names_by_id(db, ma_cam_bien)
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảm biến")
    if str(row.get("ma_nguoi_dung")) != str(current_user.ma_nguoi_dung) and not current_user.quan_tri_vien:
        raise HTTPException(status_code=403, detail="Không được phép truy cập dữ liệu người khác")

    return SensorOut(
        ma_cam_bien=_extract(row, "ma_cam_bien"),
        ten_cam_bien=_extract(row, "ten_cam_bien"),
        mo_ta=_extract(row, "mo_ta"),
        ngay_lap_dat=_extract(row, "ngay_lap_dat"),
        ma_may_bom=_extract(row, "ma_may_bom"),
        ten_may_bom=_extract(row, "ten_may_bom"),
        trang_thai=_extract(row, "trang_thai"),
        loai=_extract(row, "loai"),
        ten_loai_cam_bien=_extract(row, "ten_loai_cam_bien"),
        thoi_gian_tao=_extract(row, "thoi_gian_tao"),
    )


@router.put("/{ma_cam_bien}", status_code=200)
async def update_cam_bien_endpoint(
    ma_cam_bien: int,
    payload: SensorUpdate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật thông tin cảm biến (chủ sở hữu hoặc admin mới được phép chỉnh sửa)."""
    r = await get_cam_bien_by_id(db, ma_cam_bien)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảm biến")
    ma_user = r.get("ma_nguoi_dung") if hasattr(r, 'get') else getattr(r, 'ma_nguoi_dung', None)
    if str(ma_user) != str(current_user.ma_nguoi_dung) and not current_user.quan_tri_vien:
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa cảm biến này")
    await update_cam_bien(db, ma_cam_bien, payload)
    await db.commit()
    return {"message": "Cập nhật cảm biến thành công", "ma_cam_bien": ma_cam_bien}


@router.delete("/{ma_cam_bien}", status_code=200)
async def delete_cam_bien_endpoint(
    ma_cam_bien: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá cảm biến theo mã cảm biến (chủ sở hữu hoặc admin mới được phép xoá)."""
    r = await get_cam_bien_by_id(db, ma_cam_bien)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảm biến")
    ma_user = r.get("ma_nguoi_dung") if hasattr(r, 'get') else getattr(r, 'ma_nguoi_dung', None)
    if str(ma_user) != str(current_user.ma_nguoi_dung) and not current_user.quan_tri_vien:
        raise HTTPException(status_code=403, detail="Không được phép xoá cảm biến này")

    await delete_cam_bien(db, ma_cam_bien)
    await db.commit()
    
    return {"message": "Xoá cảm biến thành công", "ma_cam_bien": ma_cam_bien}
