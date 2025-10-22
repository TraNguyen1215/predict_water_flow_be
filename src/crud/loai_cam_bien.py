from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.schemas.loai_cam_bien import LoaiCamBienCreate
from typing import Optional
from src.models.loai_cam_bien import LoaiCamBien


async def list_loai_cam_bien(db: AsyncSession):
    q = select(LoaiCamBien).order_by(LoaiCamBien.ma_loai_cam_bien)
    res = await db.execute(q)
    return res.scalars().all()


async def get_loai_cam_bien_by_id(db: AsyncSession, ma_loai_cam_bien: int):
    q = select(LoaiCamBien).where(LoaiCamBien.ma_loai_cam_bien == ma_loai_cam_bien)
    res = await db.execute(q)
    return res.scalars().first()


async def create_loai_cam_bien(db: AsyncSession, payload: LoaiCamBienCreate):
    obj = LoaiCamBien(ten_loai_cam_bien=payload.ten_loai_cam_bien)
    db.add(obj)
    await db.flush()
    return obj


async def update_loai_cam_bien(db: AsyncSession, ma_loai_cam_bien: int, payload: LoaiCamBienCreate):
    obj = await get_loai_cam_bien_by_id(db, ma_loai_cam_bien)
    if not obj:
        return None
    if payload and payload.ten_loai_cam_bien:
        obj.ten_loai_cam_bien = payload.ten_loai_cam_bien
    await db.flush()
    return obj


async def delete_loai_cam_bien(db: AsyncSession, ma_loai_cam_bien: int):
    obj = await get_loai_cam_bien_by_id(db, ma_loai_cam_bien)
    if obj:
        await db.delete(obj)
