from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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
    q = (
        select(
            CamBien.ma_cam_bien.label("ma_cam_bien"),
            CamBien.ten_cam_bien.label("ten_cam_bien"),
            CamBien.mo_ta.label("mo_ta"),
            CamBien.ngay_lap_dat.label("ngay_lap_dat"),
            CamBien.thoi_gian_tao.label("thoi_gian_tao"),
            CamBien.ma_may_bom.label("ma_may_bom"),
            MayBom.ten_may_bom.label("ten_may_bom"),
            CamBien.trang_thai.label("trang_thai"),
            CamBien.loai.label("loai"),
            LoaiCamBien.ten_loai_cam_bien.label("ten_loai_cam_bien"),
        )
        .join(MayBom, CamBien.ma_may_bom == MayBom.ma_may_bom, isouter=True)
        .join(LoaiCamBien, CamBien.loai == LoaiCamBien.ma_loai_cam_bien)
        .where(CamBien.ma_nguoi_dung == ma_nd)
        .order_by(CamBien.thoi_gian_tao.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(q)
    items = res.mappings().all()

    count_q = select(func.count()).select_from(CamBien).where(CamBien.ma_nguoi_dung == ma_nd)
    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())
    return items, total


async def get_cam_bien_with_names_by_id(db: AsyncSession, ma_cam_bien: int):
    """Return a single row (labeled) with pump and type names for endpoints that need them."""
    q = (
        select(
            CamBien.ma_cam_bien.label("ma_cam_bien"),
            CamBien.ten_cam_bien.label("ten_cam_bien"),
            CamBien.ma_nguoi_dung.label("ma_nguoi_dung"),
            CamBien.mo_ta.label("mo_ta"),
            CamBien.ngay_lap_dat.label("ngay_lap_dat"),
            CamBien.thoi_gian_tao.label("thoi_gian_tao"),
            CamBien.ma_may_bom.label("ma_may_bom"),
            MayBom.ten_may_bom.label("ten_may_bom"),
            CamBien.trang_thai.label("trang_thai"),
            CamBien.loai.label("loai"),
            LoaiCamBien.ten_loai_cam_bien.label("ten_loai_cam_bien"),
        )
        .join(MayBom, CamBien.ma_may_bom == MayBom.ma_may_bom, isouter=True)
        .join(LoaiCamBien, CamBien.loai == LoaiCamBien.ma_loai_cam_bien)
        .where(CamBien.ma_cam_bien == ma_cam_bien)
    )
    res = await db.execute(q)
    return res.mappings().first()


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


async def count_cam_bien_for_user(db: AsyncSession, ma_nguoi_dung) -> int:
    """Đếm số lượng cảm biến của một người dùng"""
    q = select(func.count()).select_from(CamBien).where(CamBien.ma_nguoi_dung == ma_nguoi_dung)
    res = await db.execute(q)
    return int(res.scalar_one())
