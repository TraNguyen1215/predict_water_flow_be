from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, update, delete
from src.models.nguoi_dung import NguoiDung
from uuid import UUID
from typing import Optional


async def get_by_username(db: AsyncSession, ten_dang_nhap: str) -> Optional[NguoiDung]:
    q = select(NguoiDung).where(NguoiDung.ten_dang_nhap == ten_dang_nhap)
    res = await db.execute(q)
    return res.scalars().first()


async def get_by_id(db: AsyncSession, ma_nguoi_dung: UUID) -> Optional[NguoiDung]:
    q = select(NguoiDung).where(NguoiDung.ma_nguoi_dung == ma_nguoi_dung)
    res = await db.execute(q)
    return res.scalars().first()


async def create_user(db: AsyncSession, ten_dang_nhap: str, mat_khau_hash: str, salt: str, ho_ten: Optional[str] = None) -> NguoiDung:
    user = NguoiDung(ten_dang_nhap=ten_dang_nhap, mat_khau_hash=mat_khau_hash, salt=salt, ho_ten=ho_ten, so_dien_thoai=ten_dang_nhap)
    db.add(user)
    await db.flush()
    return user


async def update_password(db: AsyncSession, ma_nguoi_dung: UUID, mat_khau_hash: str, salt: str):
    await db.execute(
        update(NguoiDung)
        .where(NguoiDung.ma_nguoi_dung == ma_nguoi_dung)
        .values(mat_khau_hash=mat_khau_hash, salt=salt)
    )


async def update_avatar(db: AsyncSession, ma_nguoi_dung: UUID, avatar: str):
    await db.execute(
        update(NguoiDung)
        .where(NguoiDung.ma_nguoi_dung == ma_nguoi_dung)
        .values(avatar=avatar)
    )


async def delete_user(db: AsyncSession, ma_nguoi_dung: UUID):
    await db.execute(delete(NguoiDung).where(NguoiDung.ma_nguoi_dung == ma_nguoi_dung))


async def verify_user_by_pump_and_date(db: AsyncSession, ten_dang_nhap: str, ten_may_bom: str, ngay_tuoi_gan_nhat: date) -> Optional[NguoiDung]:
    """Return the most recent NguoiDung matching the username, pump name and a matching nhat_ky_may_bom.ngay value.

    This replicates the SQL join:
        nguoi_dung nd
        JOIN may_bom mb ON nd.ma_nguoi_dung = mb.ma_nguoi_dung
        JOIN nhat_ky_may_bom nk ON nk.ma_may_bom = mb.ma_may_bom
    with ordering on nk.thoi_gian_tao DESC and LIMIT 1.
    """
    from sqlalchemy import select
    from src.models.may_bom import MayBom
    from src.models.nhat_ky_may_bom import NhatKyMayBom
    
    q = (
        select(NguoiDung)
        .join(MayBom, NguoiDung.ma_nguoi_dung == MayBom.ma_nguoi_dung)
        .join(NhatKyMayBom, NhatKyMayBom.ma_may_bom == MayBom.ma_may_bom)
        .where(NguoiDung.ten_dang_nhap == ten_dang_nhap)
        .where(MayBom.ten_may_bom == ten_may_bom)
        .where((func.date(NhatKyMayBom.thoi_gian_bat) == ngay_tuoi_gan_nhat))
        .order_by(NhatKyMayBom.thoi_gian_tao.desc())
        .limit(1)
    )
    res = await db.execute(q)
    return res.scalars().first()

async def list_users(db: AsyncSession, limit: int = 50, offset: int = 0):
    q = select(NguoiDung).order_by(NguoiDung.thoi_gian_tao.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    items = res.scalars().all()

    count_q = select(func.count()).select_from(NguoiDung)
    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())
    return items, total
