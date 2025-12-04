from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime, date, time
from src.models.nhat_ky_gieo_trong import NhatKyGieoTrong


async def create_nhat_ky_gieo_trong(db: AsyncSession, payload) -> NhatKyGieoTrong:
    obj = NhatKyGieoTrong(
        ma_nguoi_dung=payload.ma_nguoi_dung,
        ten_cay_trong=payload.ten_cay_trong,
        noi_dung=payload.noi_dung,
        dien_tich_trong=payload.dien_tich_trong,
        ngay_gieo_trong=payload.ngay_gieo_trong,
        giai_doan=payload.giai_doan,
        thoi_gian_da_gieo=payload.thoi_gian_da_gieo,
        trang_thai=payload.trang_thai,
    )
    db.add(obj)
    await db.flush()
    return obj


async def list_nhat_ky_gieo_trong_for_user(db: AsyncSession, ma_nguoi_dung, limit: Optional[int], offset: int):
    q = select(NhatKyGieoTrong).where(NhatKyGieoTrong.ma_nguoi_dung == ma_nguoi_dung).order_by(NhatKyGieoTrong.thoi_gian_tao.desc())
    if limit is not None:
        q = q.limit(limit).offset(offset)
    res = await db.execute(q)
    items = res.scalars().all()

    count_q = select(func.count()).select_from(NhatKyGieoTrong).where(NhatKyGieoTrong.ma_nguoi_dung == ma_nguoi_dung)
    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())
    return items, total


async def list_nhat_ky_gieo_trong_by_date(db: AsyncSession, ma_nguoi_dung, ngay: date):
    # filter by ngay_gieo_trong if present
    q = select(NhatKyGieoTrong).where(NhatKyGieoTrong.ma_nguoi_dung == ma_nguoi_dung,
                                       NhatKyGieoTrong.ngay_gieo_trong == ngay).order_by(NhatKyGieoTrong.thoi_gian_tao.desc())
    res = await db.execute(q)
    return res.scalars().all()


async def get_nhat_ky_gieo_trong_by_id(db: AsyncSession, ma_gieo_trong: int):
    q = select(NhatKyGieoTrong).where(NhatKyGieoTrong.ma_gieo_trong == ma_gieo_trong)
    res = await db.execute(q)
    return res.scalars().first()


async def update_nhat_ky_gieo_trong(db: AsyncSession, ma_gieo_trong: int, payload):
    obj = await get_nhat_ky_gieo_trong_by_id(db, ma_gieo_trong)
    if not obj:
        return None
    if getattr(payload, 'ten_cay_trong', None) is not None:
        obj.ten_cay_trong = payload.ten_cay_trong
    if getattr(payload, 'noi_dung', None) is not None:
        obj.noi_dung = payload.noi_dung
    if getattr(payload, 'dien_tich_trong', None) is not None:
        obj.dien_tich_trong = payload.dien_tich_trong
    if getattr(payload, 'ngay_gieo_trong', None) is not None:
        obj.ngay_gieo_trong = payload.ngay_gieo_trong
    if getattr(payload, 'giai_doan', None) is not None:
        obj.giai_doan = payload.giai_doan
    if getattr(payload, 'thoi_gian_da_gieo', None) is not None:
        obj.thoi_gian_da_gieo = payload.thoi_gian_da_gieo
    if getattr(payload, 'trang_thai', None) is not None:
        obj.trang_thai = payload.trang_thai
    await db.flush()
    return obj


async def delete_nhat_ky_gieo_trong(db: AsyncSession, ma_gieo_trong: int):
    obj = await get_nhat_ky_gieo_trong_by_id(db, ma_gieo_trong)
    if obj:
        await db.delete(obj)
