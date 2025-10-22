import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.schemas.pump import PumpCreate
from typing import Optional
from src.models.may_bom import MayBom
from src.models.nguoi_dung import NguoiDung


async def create_may_bom(db: AsyncSession, ma_nd: uuid.UUID, payload: PumpCreate) -> MayBom:
    obj = MayBom(
        ten_may_bom=payload.ten_may_bom,
        mo_ta=payload.mo_ta,
        ma_iot_lk=payload.ma_iot_lk,
        che_do=payload.che_do,
        trang_thai=payload.trang_thai,
        ma_nguoi_dung=ma_nd,
    )
    db.add(obj)
    await db.flush()
    return obj


async def list_may_bom_for_user(db: AsyncSession, ma_nd, limit: int, offset: int):
    q = select(MayBom).where(MayBom.ma_nguoi_dung == ma_nd).order_by(MayBom.thoi_gian_tao.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    return res.scalars().all()


async def get_may_bom_by_id(db: AsyncSession, ma_may_bom: int):
    q = select(MayBom).where(MayBom.ma_may_bom == ma_may_bom)
    res = await db.execute(q)
    return res.scalars().first()

async def get_may_bom_by_name_and_user(db: AsyncSession, ten_may_bom: str, ma_nguoi_dung: uuid.UUID):
    q = select(MayBom).where(
        func.lower(func.trim(MayBom.ten_may_bom)) == ten_may_bom.lower().strip(),
        MayBom.ma_nguoi_dung == ma_nguoi_dung,
    )
    res = await db.execute(q)
    return res.scalars().first()


async def update_may_bom(db: AsyncSession, ma_may_bom: int, payload: PumpCreate):
    obj = await get_may_bom_by_id(db, ma_may_bom)
    if not obj:
        return None
    obj.ten_may_bom = payload.ten_may_bom
    obj.mo_ta = payload.mo_ta
    obj.ma_iot_lk = payload.ma_iot_lk
    obj.che_do = payload.che_do
    obj.trang_thai = payload.trang_thai
    await db.flush()
    return obj


async def delete_may_bom(db: AsyncSession, ma_may_bom: int):
    obj = await get_may_bom_by_id(db, ma_may_bom)
    if obj:
        await db.delete(obj)
