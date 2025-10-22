from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.schemas.data import DataCreate
from typing import Optional, List
import uuid
from src.models.du_lieu_cam_bien import DuLieuCamBien
from src.models.may_bom import MayBom


async def create_du_lieu(db: AsyncSession, payload: DataCreate) -> DuLieuCamBien:
    obj = DuLieuCamBien(
        ma_du_lieu=uuid.uuid4(),
        ma_may_bom=payload.ma_may_bom,
        ma_nguoi_dung=payload.ma_nguoi_dung,
        ngay=payload.ngay,
        luu_luong_nuoc=payload.luu_luong_nuoc,
        do_am_dat=payload.do_am_dat,
        nhiet_do=payload.nhiet_do,
        do_am=payload.do_am,
        mua=payload.mua,
        so_xung=payload.so_xung,
        tong_the_tich=payload.tong_the_tich,
        ghi_chu=payload.ghi_chu,
    )
    db.add(obj)
    await db.flush()
    return obj


async def list_du_lieu_for_user(db: AsyncSession, ma_nd, ma_may_bom: Optional[int], limit: int, offset: int) -> List[DuLieuCamBien]:
    q = select(DuLieuCamBien).join(MayBom, DuLieuCamBien.ma_may_bom == MayBom.ma_may_bom).where(MayBom.ma_nguoi_dung == str(ma_nd))
    if ma_may_bom:
        q = q.where(DuLieuCamBien.ma_may_bom == ma_may_bom)
    q = q.order_by(DuLieuCamBien.thoi_gian_tao.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    return res.scalars().all()


async def list_du_lieu_by_day(db: AsyncSession, ma_nd, ngay, ma_may_bom: Optional[int]) -> List[DuLieuCamBien]:
    q = select(DuLieuCamBien).join(MayBom, DuLieuCamBien.ma_may_bom == MayBom.ma_may_bom).where(MayBom.ma_nguoi_dung == str(ma_nd), DuLieuCamBien.ngay == ngay)
    if ma_may_bom:
        q = q.where(DuLieuCamBien.ma_may_bom == ma_may_bom)
    q = q.order_by(DuLieuCamBien.thoi_gian_tao.desc())
    res = await db.execute(q)
    return res.scalars().all()


async def get_du_lieu_by_id(db: AsyncSession, ma_du_lieu: uuid.UUID) -> Optional[DuLieuCamBien]:
    q = select(DuLieuCamBien).where(DuLieuCamBien.ma_du_lieu == ma_du_lieu)
    res = await db.execute(q)
    return res.scalars().first()


async def update_du_lieu(db: AsyncSession, ma_du_lieu: uuid.UUID, updates: dict) -> Optional[DuLieuCamBien]:
    obj = await get_du_lieu_by_id(db, ma_du_lieu)
    if not obj:
        return None
    for k, v in updates.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    await db.flush()
    return obj
