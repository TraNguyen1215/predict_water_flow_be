from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
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
