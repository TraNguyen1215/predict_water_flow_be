from typing import Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.schemas.pump import PumpCreate, PumpOut
from src.schemas.sensor import SensorOut
from src.crud.may_bom import *

router = APIRouter()


@router.post("/", status_code=201, response_model=PumpOut)
async def create_may_bom_endpoint(
    payload: PumpCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo máy bơm mới"""
    # Kiểm tra xem người dùng đã có máy bơm chưa
    pump_count = await count_may_bom_for_user(db, current_user.ma_nguoi_dung)
    if pump_count >= 1:
        raise HTTPException(status_code=400, detail="Mỗi tài khoản chỉ được có 1 máy bơm. Xoá máy bơm cũ trước khi tạo máy bơm mới")
    
    # Kiểm tra tên máy bơm đã tồn tại chưa
    existing = await get_may_bom_by_name_and_user(db, payload.ten_may_bom, current_user.ma_nguoi_dung)
    if existing:
        raise HTTPException(status_code=400, detail="Tên máy bơm đã tồn tại")
    
    ma = await create_may_bom(db, current_user.ma_nguoi_dung, payload)
    
    await db.commit()
    return PumpOut(
        ma_may_bom=getattr(ma, "ma_may_bom"),
        ten_may_bom=payload.ten_may_bom,
        mo_ta=payload.mo_ta,
        che_do=payload.che_do,
        trang_thai=payload.trang_thai,
        gioi_han_thoi_gian=payload.gioi_han_thoi_gian,
    )


@router.get("/", status_code=200)
async def list_may_bom_endpoint(
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách máy bơm"""
    if page is not None:
        offset = (page - 1) * limit

    rows, total = await list_may_bom_for_user(db, current_user.ma_nguoi_dung, limit, offset)
    items = [
        PumpOut(
            ma_may_bom=r.ma_may_bom,
            ten_may_bom=r.ten_may_bom,
            mo_ta=r.mo_ta,
            che_do=r.che_do,
            trang_thai=r.trang_thai,
            gioi_han_thoi_gian=r.gioi_han_thoi_gian,
            thoi_gian_tao=r.thoi_gian_tao,
        )
        for r in rows
    ]
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    return {"data": items, "limit": limit, "offset": offset, "page": page, "total_pages": total_pages, "total": total}


@router.get("/{ma_may_bom}", status_code=200)
async def get_may_bom_endpoint(
    ma_may_bom: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy thông tin máy bơm theo mã máy bơm (chỉ chủ sở hữu mới được phép truy cập)."""
    res = await get_may_bom_with_sensors(db, ma_may_bom)
    if not res:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")

    pump, sensors, sensor_count = res
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập dữ liệu người khác")

    return PumpOut(
        ma_may_bom=pump.ma_may_bom,
        ten_may_bom=pump.ten_may_bom,
        mo_ta=pump.mo_ta,
        che_do=pump.che_do,
        trang_thai=pump.trang_thai,
        gioi_han_thoi_gian=pump.gioi_han_thoi_gian,
        thoi_gian_tao=pump.thoi_gian_tao,
        tong_cam_bien=sensor_count,
        cam_bien=[
            SensorOut(
                ma_cam_bien=s.get("ma_cam_bien"),
                ten_cam_bien=s.get("ten_cam_bien"),
                mo_ta=s.get("mo_ta"),
                ngay_lap_dat=s.get("ngay_lap_dat"),
                thoi_gian_tao=s.get("thoi_gian_tao"),
                ma_may_bom=s.get("ma_may_bom"),
                ten_may_bom=pump.ten_may_bom,
                trang_thai=s.get("trang_thai"),
                loai=s.get("loai"),
                ten_loai_cam_bien=s.get("ten_loai_cam_bien"),
            )
            for s in sensors
        ],
    )


@router.put("/{ma_may_bom}", status_code=200)
async def update_may_bom_endpoint(
    ma_may_bom: int,
    payload: PumpCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật thông tin máy bơm (chỉ chủ sở hữu mới được phép chỉnh sửa)."""
    r = await get_may_bom_by_id(db, ma_may_bom)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa máy bơm này")

    await update_may_bom(db, ma_may_bom, payload)
    await db.commit()
    return {"message": "Cập nhật máy bơm thành công", "ma_may_bom": ma_may_bom}


@router.delete("/{ma_may_bom}", status_code=200)
async def delete_may_bom_endpoint(
    ma_may_bom: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá máy bơm (chỉ chủ sở hữu mới được phép xoá)."""
    r = await get_may_bom_by_id(db, ma_may_bom)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép xoá máy bơm này")

    await delete_may_bom(db, ma_may_bom)
    await db.commit()
    return {"message": "Xoá máy bơm thành công", "ma_may_bom": ma_may_bom}
