from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.models.du_lieu_du_bao import DuLieuDuBao


async def list_du_lieu_du_bao_for_user(db: AsyncSession, ma_nd, ma_may_bom: Optional[int], limit: Optional[int], offset: int) -> Tuple[List[DuLieuDuBao], int]:
    q = select(DuLieuDuBao).where(DuLieuDuBao.ma_nguoi_dung == ma_nd)
    if ma_may_bom:
        q = q.where(DuLieuDuBao.ma_may_bom == ma_may_bom)

    count_q = select(func.count()).select_from(DuLieuDuBao).where(DuLieuDuBao.ma_nguoi_dung == ma_nd)
    if ma_may_bom:
        count_q = count_q.where(DuLieuDuBao.ma_may_bom == ma_may_bom)

    q = q.order_by(DuLieuDuBao.thoi_gian_tao.desc())
    if limit is not None and limit >= 0:
        q = q.limit(limit).offset(offset)

    res = await db.execute(q)
    items = res.scalars().all()

    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())

    return items, total


async def create_du_lieu_du_bao(db: AsyncSession, obj_in: DuLieuDuBao) -> DuLieuDuBao:
    db.add(obj_in)
    await db.commit()
    await db.refresh(obj_in)
    return obj_in

