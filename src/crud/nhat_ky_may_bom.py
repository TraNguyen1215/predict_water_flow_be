from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.schemas.nhat_ky import NhatKyCreate
from typing import Optional
from src.models.nhat_ky_may_bom import NhatKyMayBom
from datetime import timezone


def _to_naive_utc(dt):
    """Convert a datetime to naive UTC (no tzinfo). If dt is None, return None."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def create_nhat_ky(db: AsyncSession, payload: NhatKyCreate) -> NhatKyMayBom:
    obj = NhatKyMayBom(
        ma_may_bom=payload.ma_may_bom,
        thoi_gian_bat=_to_naive_utc(payload.thoi_gian_bat),
        thoi_gian_tat=_to_naive_utc(payload.thoi_gian_tat),
        ghi_chu=payload.ghi_chu,
    )
    db.add(obj)
    await db.flush()
    return obj


async def list_nhat_ky_for_pump(db: AsyncSession, ma_may_bom: int, limit: int, offset: int):
    q = select(NhatKyMayBom).where(NhatKyMayBom.ma_may_bom == ma_may_bom).order_by(NhatKyMayBom.thoi_gian_tao.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    return res.scalars().all()


async def get_nhat_ky_by_id(db: AsyncSession, ma_nhat_ky: int):
    q = select(NhatKyMayBom).where(NhatKyMayBom.ma_nhat_ky == ma_nhat_ky)
    res = await db.execute(q)
    return res.scalars().first()


async def update_nhat_ky(db: AsyncSession, ma_nhat_ky: int, payload: NhatKyCreate):
    obj = await get_nhat_ky_by_id(db, ma_nhat_ky)
    if not obj:
        return None
    obj.thoi_gian_bat = _to_naive_utc(payload.thoi_gian_bat)
    obj.thoi_gian_tat = _to_naive_utc(payload.thoi_gian_tat)
    obj.ghi_chu = payload.ghi_chu
    await db.flush()
    return obj


async def delete_nhat_ky(db: AsyncSession, ma_nhat_ky: int):
    obj = await get_nhat_ky_by_id(db, ma_nhat_ky)
    if obj:
        await db.delete(obj)
