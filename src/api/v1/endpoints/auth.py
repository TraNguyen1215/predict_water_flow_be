import datetime
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps
from src.core import security
from src.core.config import settings
from src.schemas.user import TokenResponse
from src.crud.nguoi_dung import get_by_username, create_user, get_by_id, update_password, get_all_admins
from src.crud.thong_bao import create_notification

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

    exists = await get_by_username(db, ten_dang_nhap)
    if exists:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")

    mat_khau_hash, salt = security.get_password_hash_and_salt(mat_khau)

    user = await create_user(db, ten_dang_nhap=ten_dang_nhap, mat_khau_hash=mat_khau_hash, salt=salt, ho_ten=ho_ten)
    await db.commit()

    # Gửi thông báo tới tất cả admin về người dùng mới đăng ký
    admins = await get_all_admins(db)
    for admin in admins:
        await create_notification(
            db=db,
            ma_nguoi_dung=admin.ma_nguoi_dung,
            loai="INFO",
            muc_do="MEDIUM",
            tieu_de="Người dùng mới đăng ký",
            noi_dung=f"Người dùng '{ten_dang_nhap}' vừa đăng ký tài khoản mới. Họ tên: {ho_ten or 'Chưa cập nhật'}",
            du_lieu_lien_quan={"ten_dang_nhap": ten_dang_nhap, "ho_ten": ho_ten}
        )
    await db.commit()

    return {"message": "Đăng ký thành công", "ten_dang_nhap": user.ten_dang_nhap}


# đăng nhập người dùng
@router.post("/dang-nhap", status_code=200, response_model=TokenResponse)
async def dang_nhap_nguoi_dung(
    ten_dang_nhap: str = Body(..., embed=True),
    mat_khau: str = Body(..., embed=True),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Đăng nhập người dùng với tên đăng nhập và mật khẩu.
    Trả về access token (JWT) khi đăng nhập thành công.
    """

    nguoi_dung = await get_by_username(db, ten_dang_nhap)
    if not nguoi_dung:
        raise HTTPException(status_code=400, detail="Tên đăng nhập hoặc mật khẩu không đúng")

    if not security.verify_password(mat_khau, nguoi_dung.salt, nguoi_dung.mat_khau_hash):
        raise HTTPException(status_code=400, detail="Tên đăng nhập hoặc mật khẩu không đúng")

    token_data = {"sub": str(nguoi_dung.ma_nguoi_dung), "ten_dang_nhap": nguoi_dung.ten_dang_nhap}
    access_token = security.create_access_token(token_data)

    expire_dt = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    exp_unix = int(expire_dt.timestamp())
    expire_iso = expire_dt.replace(microsecond=0).isoformat() + "Z"

    nguoi = await get_by_id(db, nguoi_dung.ma_nguoi_dung)
    if nguoi:
        nguoi.dang_nhap_lan_cuoi = datetime.datetime.utcnow()
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

    nguoi = await get_by_id(db, current_user.ma_nguoi_dung)
    if not nguoi:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    if not security.verify_password(mat_khau_cu, nguoi.salt, nguoi.mat_khau_hash):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không đúng")

    if len(mat_khau_moi) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 6 ký tự")

    mat_khau_hash_moi, salt_moi = security.get_password_hash_and_salt(mat_khau_moi)
    await update_password(db, current_user.ma_nguoi_dung, mat_khau_hash_moi, salt_moi)
    await db.commit()

    return {"message": "Đổi mật khẩu thành công"}

#quen-mat-khau/verify
@router.post("/quen-mat-khau/verify", status_code=200)
async def verify_quen_mat_khau(
    ten_dang_nhap: str = Body(..., embed=True),
    ten_may_bom: str = Body(..., embed=True),
    ngay_tuoi_gan_nhat: datetime.date = Body(..., embed=True),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """Xác minh thông tin người dùng quên mật khẩu."""
    from src.crud.nguoi_dung import verify_user_by_pump_and_date

    nguoi_dung = await verify_user_by_pump_and_date(db, ten_dang_nhap, ten_may_bom, ngay_tuoi_gan_nhat)
    if not nguoi_dung:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng hoặc máy bơm hợp lệ")

    return {"message": "Xác minh thành công"}

# quên mật khẩu
@router.post("/quen-mat-khau/reset", status_code=200)
async def quen_mat_khau(
    ten_dang_nhap: str = Body(..., embed=True),
    mat_khau_moi: str = Body(..., embed=True),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """Đặt lại mật khẩu cho người dùng quên mật khẩu."""
    nguoi = await get_by_username(db, ten_dang_nhap)
    if not nguoi:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    if len(mat_khau_moi) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 6 ký tự")

    mat_khau_hash_moi, salt_moi = security.get_password_hash_and_salt(mat_khau_moi)
    await update_password(db, nguoi.ma_nguoi_dung, mat_khau_hash_moi, salt_moi)
    await db.commit()

    return {"message": "Đặt lại mật khẩu thành công"}