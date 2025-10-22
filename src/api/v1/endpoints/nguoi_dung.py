import datetime
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pathlib import Path
import aiofiles
import os
from src.api import deps
from src.schemas.user import UserPublic, UserUpdate
from src.crud.nguoi_dung import get_by_username, get_by_id, update_avatar, delete_user

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 4 * 1024 * 1024))

@router.put("/{ten_dang_nhap}/anh-dai-dien", status_code=200)
async def update_avatar_nguoi_dung(
    ten_dang_nhap: str,
    file: UploadFile = File(),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """
    Cập nhật ảnh đại diện cho người dùng theo mã người dùng.
    """

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400, detail="Chỉ cho phép file ảnh (JPEG, PNG, WEBP)"
        )

    nguoi_dung = await get_by_username(db, ten_dang_nhap)
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng")

    if str(ten_dang_nhap) != str(current_user.ten_dang_nhap):
        raise HTTPException(status_code=403, detail="Từ chối truy cập!")

    if nguoi_dung.avatar:
        old_path = UPLOAD_DIR / nguoi_dung.avatar
        if old_path.exists():
            old_path.unlink()

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File quá lớn. Kích thước tối đa là {} bytes".format(MAX_UPLOAD_SIZE))

    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = Path(file.filename).suffix
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", ten_dang_nhap)
    file_name = f"{now}_{safe_name}{ext}"
    file_path = UPLOAD_DIR / file_name

    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(contents)

    try:
        await file.close()
    except Exception:
        pass

    await update_avatar(db, nguoi_dung.ma_nguoi_dung, file_name)
    await db.commit()
    return {
        "message": "Cập nhật ảnh đại diện thành công!",
        "ten_dang_nhap": ten_dang_nhap,
        "avatar": file_name,
    }
    
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
        ho_ten=nguoi_dung.ho_ten,
        so_dien_thoai=nguoi_dung.so_dien_thoai,
        dia_chi=nguoi_dung.dia_chi,
        dang_nhap_lan_cuoi=nguoi_dung.dang_nhap_lan_cuoi,
        avatar=nguoi_dung.avatar,
        trang_thai=nguoi_dung.trang_thai,
        thoi_gian_tao=nguoi_dung.thoi_gian_tao,
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

    if str(ten_dang_nhap) != str(current_user.ten_dang_nhap):
        raise HTTPException(status_code=403, detail="Từ chối truy cập!")

    # update fields on ORM instance and commit
    if payload.ho_ten is not None:
        nguoi_dung.ho_ten = payload.ho_ten
    if payload.so_dien_thoai is not None:
        nguoi_dung.so_dien_thoai = payload.so_dien_thoai
    if payload.dia_chi is not None:
        nguoi_dung.dia_chi = payload.dia_chi
    await db.commit()
    return {
        "message": "Cập nhật thông tin người dùng thành công!",
        "ten_dang_nhap": ten_dang_nhap,
    }
    
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

    if str(ten_dang_nhap) != str(current_user.ten_dang_nhap):
        raise HTTPException(status_code=403, detail="Từ chối truy cập!")

    if nguoi_dung.avatar:
        old_path = UPLOAD_DIR / nguoi_dung.avatar
        if old_path.exists():
            old_path.unlink()

    await delete_user(db, nguoi_dung.ma_nguoi_dung)
    await db.commit()
    return {
        "message": "Xoá người dùng thành công!",
        "ten_dang_nhap": ten_dang_nhap,
    }