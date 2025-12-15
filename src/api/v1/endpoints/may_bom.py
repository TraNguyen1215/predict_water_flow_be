from typing import Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.schemas.pump import PumpCreate, PumpOut, PumpUpdate
from src.schemas.sensor import SensorOut
from src.crud.may_bom import *
from src.crud.cau_hinh_thiet_bi import create_cau_hinh_thiet_bi
from src.crud.nguoi_dung import get_all_admins, get_by_id as get_user_by_id
from src.crud.thong_bao import create_notification

router = APIRouter()


@router.post("/", status_code=201, response_model=PumpOut)
async def create_may_bom_endpoint(
    payload: PumpCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo máy bơm mới"""
    # Xác định người dùng mục tiêu
    if current_user.quan_tri_vien:
        target_user_id = payload.ma_nguoi_dung
    else:
        target_user_id = current_user.ma_nguoi_dung

    # Kiểm tra xem người dùng đã có máy bơm chưa
    if target_user_id:
        pump_count = await count_may_bom_for_user(db, target_user_id)
        if pump_count >= 1:
            raise HTTPException(status_code=400, detail="Mỗi tài khoản chỉ được có 1 máy bơm. Xoá máy bơm cũ trước khi tạo máy bơm mới")
        
        # Kiểm tra tên máy bơm đã tồn tại chưa
        existing = await get_may_bom_by_name_and_user(db, payload.ten_may_bom, target_user_id)
        if existing:
            raise HTTPException(status_code=400, detail="Tên máy bơm đã tồn tại")
    
    ma = await create_may_bom(db, target_user_id, payload)
    
    pump_id = getattr(ma, "ma_may_bom")
    
    # Tự động tạo cấu hình thiết bị với tất cả giá trị ngưỡng = 0
    await create_cau_hinh_thiet_bi(db, pump_id, {
        "do_am_toi_thieu": 0,
        "do_am_toi_da": 0,
        "nhiet_do_toi_da": 0,
        "luu_luong_toi_thieu": 0,
        "gio_bat_dau": 0,
        "gio_ket_thuc": 0,
        "tan_suat_gui_du_lieu": 0,
    })
    
    await db.commit()
    
    # Gửi thông báo tới tất cả admin về tạo máy bơm
    admins = await get_all_admins(db)
    user = await get_user_by_id(db, current_user.ma_nguoi_dung)
    user_name = user.ho_ten or user.ten_dang_nhap if user else "Người dùng"
    
    for admin in admins:
        await create_notification(
            db=db,
            ma_nguoi_dung=admin.ma_nguoi_dung,
            loai="INFO",
            muc_do="MEDIUM",
            tieu_de="Thiết bị mới được gán",
            noi_dung=f"Người dùng '{user_name}' vừa được gán thiết bị '{payload.ten_may_bom}'.",
            ma_thiet_bi=pump_id,
            du_lieu_lien_quan={"ma_may_bom": pump_id, "ten_may_bom": payload.ten_may_bom}
        )
    
    # Gửi thông báo INFO tới user về thiết bị được gán
    await create_notification(
        db=db,
        ma_nguoi_dung=current_user.ma_nguoi_dung,
        loai="INFO",
        muc_do="MEDIUM",
        tieu_de="Thiết bị được gán thành công",
        noi_dung=f"Bạn vừa được gán thiết bị '{payload.ten_may_bom}'. Thiết bị này sẽ giúp bạn theo dõi và quản lý hệ thống tưới.",
        ma_thiet_bi=pump_id,
        du_lieu_lien_quan={"ma_may_bom": pump_id, "ten_may_bom": payload.ten_may_bom}
    )
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
    """Danh sách máy bơm (admin có thể xem tất cả, user chỉ xem của mình)"""
    if page is not None:
        offset = (page - 1) * limit

    # Admin xem tất cả, user chỉ xem của mình
    if current_user.quan_tri_vien:
        from src.crud.may_bom import list_all_may_bom
        rows, total = await list_all_may_bom(db, limit, offset)
    else:
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
    """Lấy thông tin máy bơm theo mã máy bơm (chủ sở hữu hoặc admin mới được phép truy cập)."""
    res = await get_may_bom_with_sensors(db, ma_may_bom)
    if not res:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")

    pump, sensors, sensor_count = res
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung) and not current_user.quan_tri_vien:
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
    payload: PumpUpdate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật thông tin máy bơm (chủ sở hữu hoặc admin mới được phép chỉnh sửa)."""
    r = await get_may_bom_by_id(db, ma_may_bom)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung) and not current_user.quan_tri_vien:
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
    """Xoá máy bơm (chủ sở hữu hoặc admin mới được phép xoá)."""
    r = await get_may_bom_by_id(db, ma_may_bom)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung) and not current_user.quan_tri_vien:
        raise HTTPException(status_code=403, detail="Không được phép xoá máy bơm này")

    await delete_may_bom(db, ma_may_bom)
    await db.commit()
    return {"message": "Xoá máy bơm thành công", "ma_may_bom": ma_may_bom}
