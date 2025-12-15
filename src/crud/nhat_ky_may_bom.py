from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.schemas.nhat_ky import NhatKyCreate
from typing import Optional
from src.models.nhat_ky_may_bom import NhatKyMayBom
from src.models.may_bom import MayBom
from datetime import timezone, datetime, time, date
from src.crud import thong_bao as crud_thong_bao


def _to_naive_utc(dt):
    """Convert a datetime to naive UTC (no tzinfo). If dt is None, return None."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def create_nhat_ky(db: AsyncSession, payload: NhatKyCreate, ma_nguoi_dung=None) -> NhatKyMayBom:
    obj = NhatKyMayBom(
        ma_may_bom=payload.ma_may_bom,
        thoi_gian_bat=_to_naive_utc(payload.thoi_gian_bat),
        thoi_gian_tat=_to_naive_utc(payload.thoi_gian_tat),
        ghi_chu=payload.ghi_chu,
    )
    db.add(obj)
    await db.flush()
    
    # Tạo thông báo nếu có ma_nguoi_dung
    if ma_nguoi_dung:
        await crud_thong_bao.create_notification(
            db,
            ma_nguoi_dung,
            loai="DEVICE",
            muc_do="INFO",
            tieu_de="Nhật ký hoạt động máy bơm đã được tạo",
            noi_dung=f"Nhật ký hoạt động từ {payload.thoi_gian_bat} đến {payload.thoi_gian_tat} đã được lưu.",
            ma_thiet_bi=payload.ma_may_bom,
            du_lieu_lien_quan={
                "thoi_gian_bat": str(payload.thoi_gian_bat),
                "thoi_gian_tat": str(payload.thoi_gian_tat),
                "ghi_chu": payload.ghi_chu,
            },
        )
    
    return obj


async def list_nhat_ky_for_pump(db: AsyncSession, ngay: Optional[date],  ma_may_bom: int, limit: int, offset: int):
    q = select(NhatKyMayBom).where(NhatKyMayBom.ma_may_bom == ma_may_bom)
    count_q = select(func.count()).select_from(NhatKyMayBom).where(NhatKyMayBom.ma_may_bom == ma_may_bom)

    if ngay:
        start = datetime.combine(ngay, time.min)
        end = datetime.combine(ngay, time.max)
        q = q.where(NhatKyMayBom.thoi_gian_tao >= start, NhatKyMayBom.thoi_gian_tao <= end)
        count_q = count_q.where(NhatKyMayBom.thoi_gian_tao >= start, NhatKyMayBom.thoi_gian_tao <= end)

    q = q.order_by(NhatKyMayBom.thoi_gian_tao.desc()).limit(limit).offset(offset)
    
    res = await db.execute(q)
    items = res.scalars().all()

    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())
    return items, total

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
