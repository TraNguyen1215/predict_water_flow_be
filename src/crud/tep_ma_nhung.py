from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from src.models.tep_ma_nhung import TepMaNhung
from src.schemas.tep_ma_nhung import TepMaNhungCreate, TepMaNhungUpdate


async def list_tep_ma_nhung(db: AsyncSession, limit: int = 50, offset: int = 0) -> Tuple[List[TepMaNhung], int]:
    q = select(TepMaNhung).order_by(TepMaNhung.thoi_gian_tao.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    rows = res.scalars().all()

    count_q = select(func.count()).select_from(TepMaNhung)
    total = int((await db.execute(count_q)).scalar_one())
    return rows, total


async def get_tep_ma_nhung_by_id(db: AsyncSession, ma_tep_ma_nhung: int) -> Optional[TepMaNhung]:
    q = select(TepMaNhung).where(TepMaNhung.ma_tep_ma_nhung == ma_tep_ma_nhung)
    res = await db.execute(q)
    return res.scalars().first()


async def create_tep_ma_nhung(db: AsyncSession, payload: TepMaNhungCreate) -> TepMaNhung:
    obj = TepMaNhung(
        ten_tep=payload.ten_tep,
        phien_ban=payload.phien_ban,
        mo_ta=payload.mo_ta,
    )
    db.add(obj)
    await db.flush()
    return obj


async def update_tep_ma_nhung(db: AsyncSession, ma_tep_ma_nhung: int, payload: TepMaNhungUpdate) -> Optional[TepMaNhung]:
    obj = await get_tep_ma_nhung_by_id(db, ma_tep_ma_nhung)
    if not obj:
        return None

    if payload.ten_tep is not None:
        obj.ten_tep = payload.ten_tep
    if payload.phien_ban is not None:
        obj.phien_ban = payload.phien_ban
    if payload.mo_ta is not None:
        obj.mo_ta = payload.mo_ta

    await db.flush()
    return obj


async def delete_tep_ma_nhung(db: AsyncSession, ma_tep_ma_nhung: int) -> bool:
    obj = await get_tep_ma_nhung_by_id(db, ma_tep_ma_nhung)
    if not obj:
        return False
    await db.delete(obj)
    return True
