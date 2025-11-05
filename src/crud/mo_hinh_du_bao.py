from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from src.models.mo_hinh_du_bao import MoHinhDuBao
from src.schemas.mo_hinh_du_bao import MoHinhDuBaoCreate, MoHinhDuBaoUpdate


async def list_mo_hinh_du_bao(db: AsyncSession, limit: int = 50, offset: int = 0) -> Tuple[List[MoHinhDuBao], int]:
    q = select(MoHinhDuBao).order_by(MoHinhDuBao.thoi_gian_tao.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    rows = res.scalars().all()

    count_q = select(func.count()).select_from(MoHinhDuBao)
    total = int((await db.execute(count_q)).scalar_one())
    return rows, total


async def get_mo_hinh_du_bao_by_id(db: AsyncSession, ma_mo_hinh: int) -> Optional[MoHinhDuBao]:
    q = select(MoHinhDuBao).where(MoHinhDuBao.ma_mo_hinh == ma_mo_hinh)
    res = await db.execute(q)
    return res.scalars().first()


async def create_mo_hinh_du_bao(db: AsyncSession, payload: MoHinhDuBaoCreate) -> MoHinhDuBao:
    obj = MoHinhDuBao(
        ten_mo_hinh=payload.ten_mo_hinh,
        phien_ban=payload.phien_ban,
        trang_thai=payload.trang_thai,
        thoi_gian_tao=datetime.now()
    )
    db.add(obj)
    await db.flush()
    return obj


async def update_mo_hinh_du_bao(db: AsyncSession, ma_mo_hinh: int, payload: MoHinhDuBaoUpdate) -> Optional[MoHinhDuBao]:
    obj = await get_mo_hinh_du_bao_by_id(db, ma_mo_hinh)
    if not obj:
        return None

    if payload.ten_mo_hinh is not None:
        obj.ten_mo_hinh = payload.ten_mo_hinh
    if payload.phien_ban is not None:
        obj.phien_ban = payload.phien_ban
    if payload.trang_thai is not None:
        obj.trang_thai = payload.trang_thai

    await db.flush()
    return obj


async def delete_mo_hinh_du_bao(db: AsyncSession, ma_mo_hinh: int) -> bool:
    obj = await get_mo_hinh_du_bao_by_id(db, ma_mo_hinh)
    if not obj:
        return False
    await db.delete(obj)
    return True
