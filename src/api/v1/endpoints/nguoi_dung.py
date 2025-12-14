import datetime
import re
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.schemas.pump import PumpOut
from src.schemas.sensor import SensorOut
from src.schemas.user import UserPublic, UserUpdate
from src.crud.nguoi_dung import get_by_username, get_by_id, delete_user, list_users, update_password, get_all_admins
from src.core import security
from src.crud.thong_bao import create_notification

router = APIRouter()

# Lấy danh sách người dùng (chỉ admin)
@router.get("/", status_code=200)
async def list_nguoi_dung(
    limit: int = 50,
    offset: int = 0,
    page: Optional[int] = None,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Trả về danh sách người dùng. Chỉ admin mới được phép truy cập."""
    # Kiểm tra quyền admin
    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới có quyền xem danh sách người dùng")

    if page is not None:
        offset = (page - 1) * limit

    rows, total, pumps_map, sensors_map, pump_counts, sensor_counts = await list_users(db, limit=limit, offset=offset)
    items = [
        UserPublic(
            ma_nguoi_dung=r.ma_nguoi_dung,
            ten_dang_nhap=r.ten_dang_nhap,
            ho_ten=r.ho_ten,
            so_dien_thoai=r.so_dien_thoai,
            dia_chi=r.dia_chi,
            dang_nhap_lan_cuoi=r.dang_nhap_lan_cuoi,
            trang_thai=r.trang_thai,
            thoi_gian_tao=r.thoi_gian_tao,
            quan_tri_vien=r.quan_tri_vien,
            may_bom=[
                PumpOut(
                    ma_may_bom=pump_row.get("ma_may_bom"),
                    ten_may_bom=pump_row.get("ten_may_bom"),
                    mo_ta=pump_row.get("mo_ta"),
                    che_do=pump_row.get("che_do"),
                    trang_thai=pump_row.get("trang_thai"),
                    thoi_gian_tao=pump_row.get("thoi_gian_tao"),
                    tong_cam_bien=pump_row.get("tong_cam_bien", 0),
                    cam_bien=[
                        SensorOut(
                            ma_cam_bien=sensor_row.get("ma_cam_bien"),
                            ten_cam_bien=sensor_row.get("ten_cam_bien"),
                            mo_ta=sensor_row.get("mo_ta"),
                            ngay_lap_dat=sensor_row.get("ngay_lap_dat"),
                            thoi_gian_tao=sensor_row.get("thoi_gian_tao"),
                            ma_may_bom=sensor_row.get("ma_may_bom"),
                            ten_may_bom=sensor_row.get("ten_may_bom"),
                            trang_thai=sensor_row.get("trang_thai"),
                            loai=sensor_row.get("loai"),
                            ten_loai_cam_bien=sensor_row.get("ten_loai_cam_bien"),
                        )
                        for sensor_row in pump_row.get("cam_bien", [])
                    ],
                )
                for pump_row in pumps_map.get(r.ma_nguoi_dung, [])
            ],
            cam_bien=[
                SensorOut(
                    ma_cam_bien=sensor_row.get("ma_cam_bien"),
                    ten_cam_bien=sensor_row.get("ten_cam_bien"),
                    mo_ta=sensor_row.get("mo_ta"),
                    ngay_lap_dat=sensor_row.get("ngay_lap_dat"),
                    thoi_gian_tao=sensor_row.get("thoi_gian_tao"),
                    ma_may_bom=sensor_row.get("ma_may_bom"),
                    ten_may_bom=sensor_row.get("ten_may_bom"),
                    trang_thai=sensor_row.get("trang_thai"),
                    loai=sensor_row.get("loai"),
                    ten_loai_cam_bien=sensor_row.get("ten_loai_cam_bien"),
                )
                for sensor_row in sensors_map.get(r.ma_nguoi_dung, [])
            ],
            tong_may_bom=pump_counts.get(r.ma_nguoi_dung, 0),
            tong_cam_bien=sensor_counts.get(r.ma_nguoi_dung, 0),
        )
        for r in rows
    ]

    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    return {"data": items, "limit": limit, "offset": offset, "page": page, "total_pages": total_pages, "total": total}
    
# Lấy thông tin người dùng
@router.get("/{ten_dang_nhap}", status_code=200, response_model=UserPublic)
async def get_nguoi_dung(
    ten_dang_nhap: str,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """
    Lấy thông tin người dùng theo tên đăng nhập.
    """

    nguoi_dung = await get_by_username(db, ten_dang_nhap)
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng")

    if str(ten_dang_nhap) != str(current_user.ten_dang_nhap):
        raise HTTPException(status_code=403, detail="Từ chối truy cập!")

    return UserPublic(
        ma_nguoi_dung=nguoi_dung.ma_nguoi_dung,
        ten_dang_nhap=nguoi_dung.ten_dang_nhap,
        ho_ten=nguoi_dung.ho_ten,
        so_dien_thoai=nguoi_dung.so_dien_thoai,
        dia_chi=nguoi_dung.dia_chi,
        dang_nhap_lan_cuoi=nguoi_dung.dang_nhap_lan_cuoi,
        trang_thai=nguoi_dung.trang_thai,
        thoi_gian_tao=nguoi_dung.thoi_gian_tao,
        quan_tri_vien=nguoi_dung.quan_tri_vien,
    )
    
# Cập nhật thông tin người dùng
@router.put("/{ten_dang_nhap}", status_code=200)
async def update_nguoi_dung(
    ten_dang_nhap: str,
    payload: UserUpdate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """
    Cập nhật thông tin người dùng theo tên đăng nhập.
    """

    nguoi_dung = await get_by_username(db, ten_dang_nhap)
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng")

    is_admin = getattr(current_user, "quan_tri_vien", False)
    is_self = str(ten_dang_nhap) == str(current_user.ten_dang_nhap)

    if not is_admin and not is_self:
        raise HTTPException(status_code=403, detail="Từ chối truy cập!")

    if payload.quan_tri_vien is not None and not is_admin:
        raise HTTPException(status_code=403, detail="Không được phép cập nhật quyền quản trị")
    if getattr(payload, "trang_thai", None) is not None and not is_admin:
        raise HTTPException(status_code=403, detail="Không được phép cập nhật trạng thái người dùng")

    if payload.ho_ten is not None:
        nguoi_dung.ho_ten = payload.ho_ten
    if payload.so_dien_thoai is not None:
        nguoi_dung.so_dien_thoai = payload.so_dien_thoai
    if payload.dia_chi is not None:
        nguoi_dung.dia_chi = payload.dia_chi
    if payload.quan_tri_vien is not None:
        old_admin_status = nguoi_dung.quan_tri_vien
        nguoi_dung.quan_tri_vien = payload.quan_tri_vien
        
        # Gửi thông báo nếu có thay đổi quyền admin
        if old_admin_status != payload.quan_tri_vien:
            admins = await get_all_admins(db)
            status_text = "được thăng cấp thành quản trị viên" if payload.quan_tri_vien else "bị hạ cấp khỏi quyền quản trị viên"
            for admin in admins:
                await create_notification(
                    db=db,
                    ma_nguoi_dung=admin.ma_nguoi_dung,
                    loai="INFO",
                    muc_do="MEDIUM",
                    tieu_de="Thay đổi quyền quản trị viên",
                    noi_dung=f"Người dùng '{ten_dang_nhap}' vừa {status_text}.",
                    du_lieu_lien_quan={"ten_dang_nhap": ten_dang_nhap, "quan_tri_vien": payload.quan_tri_vien}
                )
    if getattr(payload, "trang_thai", None) is not None:
        nguoi_dung.trang_thai = payload.trang_thai
   
    await db.commit()
    return {
        "message": "Cập nhật thông tin người dùng thành công!",
        "ten_dang_nhap": ten_dang_nhap,
    }


@router.post("/{ten_dang_nhap}/cap-lai-mat-khau", status_code=200)
async def cap_lai_mat_khau_cho_nguoi_dung(
    ten_dang_nhap: str,
    mat_khau_moi: str = Body(..., embed=True),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Admin cấp lại mật khẩu cho người dùng. Chỉ admin mới có quyền."""

    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới có quyền cấp lại mật khẩu")

    nguoi_dung = await get_by_username(db, ten_dang_nhap)
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng")

    if len(mat_khau_moi) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 6 ký tự")

    mat_khau_hash, salt = security.get_password_hash_and_salt(mat_khau_moi)
    await update_password(db, nguoi_dung.ma_nguoi_dung, mat_khau_hash, salt)
    await db.commit()

    return {"message": "Cấp lại mật khẩu thành công", "ten_dang_nhap": ten_dang_nhap}
    
# Xoá người dùng
@router.delete("/{ten_dang_nhap}", status_code=200)
async def delete_nguoi_dung(
    ten_dang_nhap: str,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """
    Xoá người dùng theo tên đăng nhập.
    """

    nguoi_dung = await get_by_username(db, ten_dang_nhap)
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng")

    if not getattr(current_user, "quan_tri_vien", False) and str(ten_dang_nhap) != str(current_user.ten_dang_nhap):
        raise HTTPException(status_code=403, detail="Từ chối truy cập!")

    await delete_user(db, nguoi_dung.ma_nguoi_dung)
    await db.commit()
    
    # Gửi thông báo tới tất cả admin về xóa user
    admins = await get_all_admins(db)
    for admin in admins:
        await create_notification(
            db=db,
            ma_nguoi_dung=admin.ma_nguoi_dung,
            loai="INFO",
            muc_do="MEDIUM",
            tieu_de="Người dùng được xoá",
            noi_dung=f"Người dùng '{ten_dang_nhap}' (họ tên: {nguoi_dung.ho_ten or 'Chưa cập nhật'}) vừa bị xoá khỏi hệ thống.",
            du_lieu_lien_quan={"ten_dang_nhap": ten_dang_nhap, "ma_nguoi_dung": str(nguoi_dung.ma_nguoi_dung)}
        )
    await db.commit()
    
    return {
        "message": "Xoá người dùng thành công!",
        "ten_dang_nhap": ten_dang_nhap,
    }