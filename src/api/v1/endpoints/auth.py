import datetime
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.core import security
from src.core.config import settings

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
            "INSERT INTO nguoi_dung(ma_nguoi_dung, ten_dang_nhap, mat_khau_hash, salt, ho_ten, so_dien_thoai, thoi_gian_tao) VALUES(:ma_nguoi_dung, :ten_dang_nhap, :mat_khau_hash, :salt, :ho_ten, :so_dien_thoai, NOW())"
        ),
        {
            "ma_nguoi_dung": uuid.uuid4(),
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

    expire_dt = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    exp_unix = int(expire_dt.timestamp())
    expire_iso = expire_dt.replace(microsecond=0).isoformat() + "Z"

    await db.execute(
        text("UPDATE nguoi_dung SET dang_nhap_lan_cuoi = :now WHERE ma_nguoi_dung = :ma_nguoi_dung"),
        {"now": datetime.datetime.utcnow(), "ma_nguoi_dung": nguoi_dung.ma_nguoi_dung},
    )
    await db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "details": "Đăng nhập thành công",
        "exp": exp_unix,
        "expires_at": expire_iso,
    }


# đổi mật khẩu
@router.post("/doi-mat-khau", status_code=200)
async def doi_mat_khau(
    mat_khau_cu: str = Body(..., embed=True),
    mat_khau_moi: str = Body(..., embed=True),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Đổi mật khẩu cho người dùng đã đăng nhập."""

    result = await db.execute(
        text(
            "SELECT mat_khau_hash, salt FROM nguoi_dung WHERE ma_nguoi_dung = :ma_nguoi_dung"
        ),
        {"ma_nguoi_dung": current_user.ma_nguoi_dung},
    )

    nguoi_dung = result.fetchone()
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    if not security.verify_password(mat_khau_cu, nguoi_dung.salt, nguoi_dung.mat_khau_hash):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không đúng")

    if len(mat_khau_moi) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 6 ký tự")

    mat_khau_hash_moi, salt_moi = security.get_password_hash_and_salt(mat_khau_moi)

    await db.execute(
        text(
            "UPDATE nguoi_dung SET mat_khau_hash = :mat_khau_hash, salt = :salt, thoi_gian_cap_nhat = NOW() WHERE ma_nguoi_dung = :ma_nguoi_dung"
        ),
        {
            "mat_khau_hash": mat_khau_hash_moi,
            "salt": salt_moi,
            "ma_nguoi_dung": current_user.ma_nguoi_dung,
        },
    )

    await db.commit()

    return {"message": "Đổi mật khẩu thành công"}

# quên mật khẩu
@router.post("/quen-mat-khau", status_code=200)
async def quen_mat_khau(
    ten_dang_nhap: str = Body(..., embed=True),
    ten_may_bom: str = Body(..., embed=True),
    ngay_tuoi_gan_nhat: datetime.date = Body(..., embed=True),
    mat_khau_moi: str = Body(..., embed=True),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """Đặt lại mật khẩu cho người dùng quên mật khẩu."""
    result = await db.execute(
        text(
            """
            SELECT nd.ma_nguoi_dung
            FROM nguoi_dung nd
            JOIN may_bom mb ON nd.ma_nguoi_dung = mb.ma_nguoi_dung
            JOIN nhat_ky_may_bom nk ON nk.ma_may_bom = mb.ma_may_bom
            WHERE nd.ten_dang_nhap = :ten_dang_nhap
                AND mb.ten_may_bom = :ten_may_bom
                AND nk.ngay = :ngay_tuoi_gan_nhat
            ORDER BY nk.thoi_gian_tao DESC
            LIMIT 1
        """
        ),
        {"ten_dang_nhap": ten_dang_nhap, "ten_may_bom": ten_may_bom, "ngay_tuoi_gan_nhat": ngay_tuoi_gan_nhat},
    )

    nguoi_dung = result.fetchone()
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng hoặc máy bơm hợp lệ")

    if len(mat_khau_moi) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 6 ký tự")

    mat_khau_hash_moi, salt_moi = security.get_password_hash_and_salt(mat_khau_moi)

    await db.execute(
        text(
            "UPDATE nguoi_dung SET mat_khau_hash = :mat_khau_hash, salt = :salt, thoi_gian_cap_nhat = NOW() WHERE ma_nguoi_dung = :ma_nguoi_dung"
        ),
        {
            "mat_khau_hash": mat_khau_hash_moi,
            "salt": salt_moi,
            "ma_nguoi_dung": nguoi_dung.ma_nguoi_dung,
        },
    )

    await db.commit()

    return {"message": "Đặt lại mật khẩu thành công"}