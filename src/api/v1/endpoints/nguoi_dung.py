import datetime
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pathlib import Path
import shutil
from src.api import deps

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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

    result = await db.execute(
        text(
            "SELECT ma_nguoi_dung, avatar FROM nguoi_dung WHERE ten_dang_nhap = :ten_dang_nhap"
        ),
        {"ten_dang_nhap": ten_dang_nhap},
    )

    nguoi_dung = result.fetchone()
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng")

    if str(ten_dang_nhap) != str(current_user.ten_dang_nhap):
        raise HTTPException(status_code=403, detail="Từ chối truy cập!")

    if nguoi_dung.avatar:
        old_path = UPLOAD_DIR / nguoi_dung.avatar
        if old_path.exists():
            old_path.unlink()

    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = Path(file.filename).suffix
    file_name = f"{now}_{ten_dang_nhap}{ext}"
    file_path = UPLOAD_DIR / file_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    await db.execute(
        text(
            """
            UPDATE nguoi_dung
            SET avatar = :avatar,
                thoi_gian_cap_nhat = NOW()
            WHERE ma_nguoi_dung = :ma_nguoi_dung
        """
        ),
        {"avatar": file_name, "ten_dang_nhap": ten_dang_nhap},
    )

    await db.commit()
    return {
        "message": "Cập nhật ảnh đại diện thành công!",
        "ten_dang_nhap": ten_dang_nhap,
        "avatar": file_name,
    }
    
# Lấy thông tin người dùng
@router.get("/{ten_dang_nhap}", status_code=200)
async def get_nguoi_dung(
    ten_dang_nhap: str,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """
    Lấy thông tin người dùng theo tên đăng nhập.
    """

    result = await db.execute(
        text(
            "SELECT * FROM nguoi_dung WHERE ten_dang_nhap = :ten_dang_nhap"
        ),
        {"ten_dang_nhap": ten_dang_nhap},
    )

    nguoi_dung = result.fetchone()
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng")

    if str(ten_dang_nhap) != str(current_user.ten_dang_nhap):
        raise HTTPException(status_code=403, detail="Từ chối truy cập!")

    return {
        "ma_nguoi_dung": nguoi_dung.ma_nguoi_dung,
        "ho_ten": nguoi_dung.ho_ten,
        "so_dien_thoai": nguoi_dung.so_dien_thoai,
        "dia_chi": nguoi_dung.dia_chi,
        "dang_nhap_lan_cuoi": nguoi_dung.dang_nhap_lan_cuoi,
        "avatar": nguoi_dung.avatar,
        "trang_thai": nguoi_dung.trang_thai,
        "thoi_gian_tao": nguoi_dung.thoi_gian_tao,
    }
    
# Cập nhật thông tin người dùng
@router.put("/{ten_dang_nhap}", status_code=200)
async def update_nguoi_dung(
    ten_dang_nhap: str,
    ho_ten: str = Body(...),
    so_dien_thoai: str = Body(...),
    dia_chi: str = Body(...),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """
    Cập nhật thông tin người dùng theo tên đăng nhập.
    """

    result = await db.execute(
        text(
            "SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = :ten_dang_nhap"
        ),
        {"ten_dang_nhap": ten_dang_nhap},
    )

    nguoi_dung = result.fetchone()
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng")

    if str(ten_dang_nhap) != str(current_user.ten_dang_nhap):
        raise HTTPException(status_code=403, detail="Từ chối truy cập!")

    await db.execute(
        text(
            """
            UPDATE nguoi_dung
            SET ho_ten = :ho_ten,
                so_dien_thoai = :so_dien_thoai,
                dia_chi = :dia_chi,
                thoi_gian_cap_nhat = NOW()
            WHERE ma_nguoi_dung = :ma_nguoi_dung
        """
        ),
        {
            "ho_ten": ho_ten,
            "so_dien_thoai": so_dien_thoai,
            "dia_chi": dia_chi,
            "ten_dang_nhap": ten_dang_nhap,
        },
    )

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

    result = await db.execute(
        text(
            "SELECT ma_nguoi_dung, avatar FROM nguoi_dung WHERE ten_dang_nhap = :ten_dang_nhap"
        ),
        {"ten_dang_nhap": ten_dang_nhap},
    )

    nguoi_dung = result.fetchone()
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu người dùng")

    if str(ten_dang_nhap) != str(current_user.ten_dang_nhap):
        raise HTTPException(status_code=403, detail="Từ chối truy cập!")

    if nguoi_dung.avatar:
        old_path = UPLOAD_DIR / nguoi_dung.avatar
        if old_path.exists():
            old_path.unlink()

    await db.execute(
        text(
            "DELETE FROM nguoi_dung WHERE ten_dang_nhap = :ten_dang_nhap"
        ),
        {"ten_dang_nhap": ten_dang_nhap},
    )

    await db.commit()
    return {
        "message": "Xoá người dùng thành công!",
        "ten_dang_nhap": ten_dang_nhap,
    }