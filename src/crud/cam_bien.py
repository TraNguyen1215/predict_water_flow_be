from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from src.schemas.sensor import SensorCreate
from src.models.cam_bien import CamBien
from src.models.may_bom import MayBom
from src.models.loai_cam_bien import LoaiCamBien


async def create_cam_bien(db: AsyncSession, ma_nd, payload: SensorCreate) -> CamBien:
    obj = CamBien(ma_nguoi_dung=ma_nd, ten_cam_bien=payload.ten_cam_bien, mo_ta=payload.mo_ta, ngay_lap_dat=payload.ngay_lap_dat, ma_may_bom=payload.ma_may_bom, loai=payload.loai)
    db.add(obj)
    await db.flush()
    return obj


async def list_cam_bien_for_user(db: AsyncSession, ma_nd, limit: int, offset: int):
    q = select(CamBien).where(CamBien.ma_nguoi_dung == ma_nd).order_by(CamBien.thoi_gian_tao.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    return res.scalars().all()


async def get_cam_bien_by_id(db: AsyncSession, ma_cam_bien: int):
    q = select(CamBien).where(CamBien.ma_cam_bien == ma_cam_bien)
    res = await db.execute(q)
    return res.scalars().first()


async def update_cam_bien(db: AsyncSession, ma_cam_bien: int, payload: SensorCreate):
    obj = await get_cam_bien_by_id(db, ma_cam_bien)
    if not obj:
        return None
    obj.ten_cam_bien = payload.ten_cam_bien
    obj.mo_ta = payload.mo_ta
    obj.ma_may_bom = payload.ma_may_bom
    obj.ngay_lap_dat = payload.ngay_lap_dat
    if hasattr(payload, "trang_thai"):
        obj.trang_thai = payload.trang_thai
    obj.loai = payload.loai
    await db.flush()
    return obj


async def delete_cam_bien(db: AsyncSession, ma_cam_bien: int):
    obj = await get_cam_bien_by_id(db, ma_cam_bien)
    if obj:
        await db.delete(obj)
