from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.models.cau_hinh_thiet_bi import CauHinhThietBi
from src.models.may_bom import MayBom
from src.crud import thong_bao as crud_thong_bao


async def create_cau_hinh_thiet_bi(db: AsyncSession, ma_thiet_bi: int, payload: dict) -> CauHinhThietBi:
    """Create a new device configuration record."""
    obj = CauHinhThietBi(
        ma_thiet_bi=ma_thiet_bi,
        do_am_toi_thieu=payload.get("do_am_toi_thieu"),
        do_am_toi_da=payload.get("do_am_toi_da"),
        nhiet_do_toi_da=payload.get("nhiet_do_toi_da"),
        luu_luong_toi_thieu=payload.get("luu_luong_toi_thieu"),
        gio_bat_dau=payload.get("gio_bat_dau"),
        gio_ket_thuc=payload.get("gio_ket_thuc"),
        tan_suat_gui_du_lieu=payload.get("tan_suat_gui_du_lieu"),
    )
    db.add(obj)
    await db.flush()
    return obj


async def get_cau_hinh_by_id(db: AsyncSession, ma_cau_hinh: int) -> CauHinhThietBi:
    """Get configuration by ID."""
    q = select(CauHinhThietBi).where(CauHinhThietBi.ma_cau_hinh == ma_cau_hinh)
    res = await db.execute(q)
    return res.scalars().first()


async def get_cau_hinh_by_thiet_bi(db: AsyncSession, ma_thiet_bi: int) -> CauHinhThietBi:
    """Get configuration by device ID (ma_thiet_bi)."""
    q = select(CauHinhThietBi).where(CauHinhThietBi.ma_thiet_bi == ma_thiet_bi)
    res = await db.execute(q)
    return res.scalars().first()


async def list_cau_hinh(db: AsyncSession, limit: int = 10, offset: int = 0):
    """List all device configurations."""
    q = select(CauHinhThietBi).order_by(CauHinhThietBi.thoi_gian_tao.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    items = res.scalars().all()

    count_q = select(func.count()).select_from(CauHinhThietBi)
    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())
    return items, total


async def update_cau_hinh(db: AsyncSession, ma_cau_hinh: int, payload: dict) -> CauHinhThietBi:
    """Update device configuration."""
    obj = await get_cau_hinh_by_id(db, ma_cau_hinh)
    if not obj:
        return None
    
    pump_q = select(MayBom).where(MayBom.ma_may_bom == obj.ma_thiet_bi)
    pump_res = await db.execute(pump_q)
    pump = pump_res.scalars().first()
    
    old_values = {}
    changed_fields = []
    
    for key, value in payload.items():
        if hasattr(obj, key) and key not in ["ma_cau_hinh", "ma_thiet_bi"]:
            old_value = getattr(obj, key)
            if old_value != value:
                old_values[key] = old_value
                changed_fields.append(f"{key}: {old_value} → {value}")
            setattr(obj, key, value)
    
    await db.flush()
    
    if changed_fields and pump:
        await crud_thong_bao.create_notification(
            db,
            pump.ma_nguoi_dung,
            loai="ALERT",
            muc_do="MEDIUM",
            tieu_de=f"Cấu hình máy bơm '{pump.ten_may_bom}' đã được cập nhật",
            noi_dung=f"Các tham số cấu hình đã được thay đổi:\n" + "\n".join(changed_fields),
            ma_thiet_bi=obj.ma_thiet_bi,
            du_lieu_lien_quan=payload,
        )
    
    return obj


async def delete_cau_hinh(db: AsyncSession, ma_cau_hinh: int) -> bool:
    """Delete device configuration."""
    obj = await get_cau_hinh_by_id(db, ma_cau_hinh)
    if not obj:
        return False
    
    await db.delete(obj)
    await db.flush()
    return True
