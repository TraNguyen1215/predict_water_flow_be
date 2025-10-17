import datetime
import re
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.core import security

router = APIRouter()

@router.post("/dang-ky", status_code=201)
async def register_nguoi_dung(
    ten_dang_nhap: str = Body(..., embed=True),
    mat_khau: str = Body(..., embed=True),
    ho_ten: str | None = Body(None, embed=True),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """Đăng ký người dùng mới. Mật khẩu sẽ được hash trước khi lưu."""

    if not re.match(r"^[a-zA-Z0-9_.-]{3,50}$", ten_dang_nhap):
        raise HTTPException(status_code=400, detail="Tên đăng nhập không hợp lệ")

    if len(mat_khau) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")

    result = await db.execute(
        text(
            "SELECT ma_nguoi_dung FROM nguoi_dung WHERE ten_dang_nhap = :ten_dang_nhap"
        ),
        {"ten_dang_nhap": ten_dang_nhap},
    )
    exists = result.fetchone()
    if exists:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")


    # Create salted hash and store both hash and salt in DB
    mat_khau_hash, salt = security.get_password_hash_and_salt(mat_khau)

    await db.execute(
        text(
            "INSERT INTO nguoi_dung(ten_dang_nhap, mat_khau_hash, salt, ho_ten, so_dien_thoai, thoi_gian_tao) VALUES(:ten_dang_nhap, :mat_khau_hash, :salt, :ho_ten, :so_dien_thoai, NOW())"
        ),
        {
            "ten_dang_nhap": ten_dang_nhap,
            "mat_khau_hash": mat_khau_hash,
            "salt": salt,
            "ho_ten": ho_ten,
            "so_dien_thoai": ten_dang_nhap,
        },
    )

    await db.commit()

    return {"message": "Đăng ký thành công", "ten_dang_nhap": ten_dang_nhap}


# đăng nhập người dùng
@router.post("/dang-nhap", status_code=200)
async def dang_nhap_nguoi_dung(
    ten_dang_nhap: str = Body(..., embed=True),
    mat_khau: str = Body(..., embed=True),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Đăng nhập người dùng với tên đăng nhập và mật khẩu.
    Trả về access token (JWT) khi đăng nhập thành công.
    """

    result = await db.execute(
        text(
            "SELECT ma_nguoi_dung, ten_dang_nhap, mat_khau_hash, salt FROM nguoi_dung WHERE ten_dang_nhap = :ten_dang_nhap"
        ),
        {"ten_dang_nhap": ten_dang_nhap},
    )

    nguoi_dung = result.fetchone()
    if not nguoi_dung:
        raise HTTPException(status_code=400, detail="Tên đăng nhập hoặc mật khẩu không đúng")

    if not security.verify_password(mat_khau, nguoi_dung.salt, nguoi_dung.mat_khau_hash):
        raise HTTPException(status_code=400, detail="Tên đăng nhập hoặc mật khẩu không đúng")

    token_data = {"sub": str(nguoi_dung.ma_nguoi_dung), "ten_dang_nhap": nguoi_dung.ten_dang_nhap}
    access_token = security.create_access_token(token_data)

    await db.execute(
        text("UPDATE nguoi_dung SET dang_nhap_lan_cuoi = :now WHERE ma_nguoi_dung = :ma_nguoi_dung"),
        {"now": datetime.datetime.utcnow(), "ma_nguoi_dung": nguoi_dung.ma_nguoi_dung},
    )
    await db.commit()

    return {"access_token": access_token, "token_type": "bearer"}

