from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func
from uuid import UUID
from src.models.thong_bao import ThongBao
from src.schemas.thong_bao import ThongBaoCreate, ThongBaoUpdate


async def create_notification(
    db: AsyncSession,
    ma_nguoi_dung: UUID,
    loai: str,
    muc_do: str,
    tieu_de: str,
    noi_dung: str,
    ma_thiet_bi: Optional[int] = None,
    du_lieu_lien_quan: Optional[Any] = None,
) -> ThongBao:
    """Helper function to create notification from other operations"""
    notification = ThongBao(
        ma_nguoi_dung=ma_nguoi_dung,
        ma_thiet_bi=ma_thiet_bi,
        loai=loai,
        muc_do=muc_do,
        tieu_de=tieu_de,
        noi_dung=noi_dung,
        du_lieu_lien_quan=du_lieu_lien_quan,
    )
    db.add(notification)
    await db.flush()
    return notification


async def create(db: AsyncSession, obj_in: ThongBaoCreate) -> ThongBao:
    db_obj = ThongBao(
        ma_nguoi_dung=obj_in.ma_nguoi_dung,
        ma_thiet_bi=obj_in.ma_thiet_bi,
        loai=obj_in.loai,
        muc_do=obj_in.muc_do,
        tieu_de=obj_in.tieu_de,
        noi_dung=obj_in.noi_dung,
        da_xem=obj_in.da_xem,
        du_lieu_lien_quan=obj_in.du_lieu_lien_quan,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_by_id(db: AsyncSession, ma_thong_bao: int) -> Optional[ThongBao]:
    q = select(ThongBao).where(ThongBao.ma_thong_bao == ma_thong_bao)
    res = await db.execute(q)
    return res.scalars().first()


async def get_by_user(
    db: AsyncSession, ma_nguoi_dung: UUID, skip: int = 0, limit: int = 100
) -> tuple[List[ThongBao], int]:
    # Get count
    count_q = select(func.count(ThongBao.ma_thong_bao)).where(
        ThongBao.ma_nguoi_dung == ma_nguoi_dung
    )
    count_res = await db.execute(count_q)
    total = count_res.scalar() or 0
    
    # Get data
    q = (
        select(ThongBao)
        .where(ThongBao.ma_nguoi_dung == ma_nguoi_dung)
        .order_by(desc(ThongBao.thoi_gian))
        .offset(skip)
        .limit(limit)
    )
    res = await db.execute(q)
    return res.scalars().all(), total


async def get_unread_by_user(
    db: AsyncSession, ma_nguoi_dung: UUID, skip: int = 0, limit: int = 100
) -> tuple[List[ThongBao], int]:
    # Get count
    count_q = select(func.count(ThongBao.ma_thong_bao)).where(
        (ThongBao.ma_nguoi_dung == ma_nguoi_dung) & (ThongBao.da_xem == False)
    )
    count_res = await db.execute(count_q)
    total = count_res.scalar() or 0
    
    # Get data
    q = (
        select(ThongBao)
        .where(
            (ThongBao.ma_nguoi_dung == ma_nguoi_dung) & (ThongBao.da_xem == False)
        )
        .order_by(desc(ThongBao.thoi_gian))
        .offset(skip)
        .limit(limit)
    )
    res = await db.execute(q)
    return res.scalars().all(), total


async def count_unread_by_user(db: AsyncSession, ma_nguoi_dung: UUID) -> int:
    q = select(
        func.count(ThongBao.ma_thong_bao)
    ).where((ThongBao.ma_nguoi_dung == ma_nguoi_dung) & (ThongBao.da_xem == False))
    res = await db.execute(q)
    return res.scalar() or 0


async def update(
    db: AsyncSession, ma_thong_bao: int, obj_in: ThongBaoUpdate
) -> Optional[ThongBao]:
    db_obj = await get_by_id(db, ma_thong_bao)
    if not db_obj:
        return None

    update_data = obj_in.dict(exclude_unset=True)
    q = (
        update(ThongBao)
        .where(ThongBao.ma_thong_bao == ma_thong_bao)
        .values(**update_data)
    )
    await db.execute(q)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def mark_as_read(db: AsyncSession, ma_thong_bao: int) -> Optional[ThongBao]:
    q = (
        update(ThongBao)
        .where(ThongBao.ma_thong_bao == ma_thong_bao)
        .values(da_xem=True)
    )
    await db.execute(q)
    await db.commit()
    return await get_by_id(db, ma_thong_bao)


async def mark_all_as_read(db: AsyncSession, ma_nguoi_dung: UUID) -> int:
    q = (
        update(ThongBao)
        .where((ThongBao.ma_nguoi_dung == ma_nguoi_dung) & (ThongBao.da_xem == False))
        .values(da_xem=True)
    )
    res = await db.execute(q)
    await db.commit()
    return res.rowcount


async def delete(db: AsyncSession, ma_thong_bao: int) -> bool:
    q = delete(ThongBao).where(ThongBao.ma_thong_bao == ma_thong_bao)
    res = await db.execute(q)
    await db.commit()
    return res.rowcount > 0


async def delete_by_user(db: AsyncSession, ma_nguoi_dung: UUID) -> int:
    q = delete(ThongBao).where(ThongBao.ma_nguoi_dung == ma_nguoi_dung)
    res = await db.execute(q)
    await db.commit()
    return res.rowcount
