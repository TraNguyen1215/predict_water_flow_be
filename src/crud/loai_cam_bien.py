from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from src.schemas.loai_cam_bien import LoaiCamBienCreate
from typing import Optional
from src.models.loai_cam_bien import LoaiCamBien
from src.models.cam_bien import CamBien


async def list_loai_cam_bien(db: AsyncSession, limit: int = 100, offset: int = 0):
    from sqlalchemy.orm import aliased
    from src.models.may_bom import MayBom
    from src.models.nguoi_dung import NguoiDung

    # Get basic sensor types
    q = select(LoaiCamBien).order_by(LoaiCamBien.ma_loai_cam_bien).limit(limit).offset(offset)
    res = await db.execute(q)
    items = res.scalars().all()

    count_q = select(func.count()).select_from(LoaiCamBien)
    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())

    # Get sensors for each type
    type_ids = [item.ma_loai_cam_bien for item in items]
    sensors_by_type = {}
    sensor_counts = {}

    if type_ids:
        sensor_q = (
            select(
                CamBien.loai,
                CamBien.ma_cam_bien,
                CamBien.ten_cam_bien,
                CamBien.mo_ta,
                CamBien.ngay_lap_dat,
                CamBien.thoi_gian_tao,
                CamBien.trang_thai,
                # Pump info
                MayBom.ma_may_bom,
                MayBom.ten_may_bom,
                MayBom.mo_ta.label("may_bom_mo_ta"),
                MayBom.trang_thai.label("may_bom_trang_thai"),
                # User info
                NguoiDung.ma_nguoi_dung,
                NguoiDung.ten_dang_nhap,
                NguoiDung.ho_ten,
            )
            .join(MayBom, CamBien.ma_may_bom == MayBom.ma_may_bom, isouter=True)
            .join(NguoiDung, CamBien.ma_nguoi_dung == NguoiDung.ma_nguoi_dung)
            .where(CamBien.loai.in_(type_ids))
            .order_by(CamBien.thoi_gian_tao.desc())
        )
        sensor_res = await db.execute(sensor_q)
        rows = sensor_res.mappings().all()
        
        for row in rows:
            type_id = row["loai"]
            if type_id not in sensors_by_type:
                sensors_by_type[type_id] = []
                sensor_counts[type_id] = 0
            
            sensor_dict = {
                "ma_cam_bien": row["ma_cam_bien"],
                "ten_cam_bien": row["ten_cam_bien"],
                "mo_ta": row["mo_ta"],
                "ngay_lap_dat": row["ngay_lap_dat"],
                "thoi_gian_tao": row["thoi_gian_tao"],
                "trang_thai": row["trang_thai"],
            }

            # Add pump info if exists
            if row["ma_may_bom"]:
                sensor_dict["may_bom"] = {
                    "ma_may_bom": row["ma_may_bom"],
                    "ten_may_bom": row["ten_may_bom"],
                    "mo_ta": row["may_bom_mo_ta"],
                    "trang_thai": row["may_bom_trang_thai"],
                }

            # Add user info
            sensor_dict["nguoi_dung"] = {
                "ma_nguoi_dung": row["ma_nguoi_dung"],
                "ten_dang_nhap": row["ten_dang_nhap"],
                "ho_ten": row["ho_ten"],
            }

            sensors_by_type[type_id].append(sensor_dict)
            sensor_counts[type_id] += 1

    # Add sensors to their respective types
    for item in items:
        type_id = item.ma_loai_cam_bien
        item.cam_bien = sensors_by_type.get(type_id, [])
        item.tong_cam_bien = sensor_counts.get(type_id, 0)

    return items, total


async def get_loai_cam_bien_by_id(db: AsyncSession, ma_loai_cam_bien: int):
    q = select(LoaiCamBien).where(LoaiCamBien.ma_loai_cam_bien == ma_loai_cam_bien)
    res = await db.execute(q)
    return res.scalars().first()


async def create_loai_cam_bien(db: AsyncSession, payload: LoaiCamBienCreate):
    obj = LoaiCamBien(ten_loai_cam_bien=payload.ten_loai_cam_bien)
    db.add(obj)
    await db.flush()
    return obj


async def update_loai_cam_bien(db: AsyncSession, ma_loai_cam_bien: int, payload: LoaiCamBienCreate):
    obj = await get_loai_cam_bien_by_id(db, ma_loai_cam_bien)
    if not obj:
        return None
    if payload and payload.ten_loai_cam_bien:
        obj.ten_loai_cam_bien = payload.ten_loai_cam_bien
    await db.flush()
    return obj


async def delete_loai_cam_bien(db: AsyncSession, ma_loai_cam_bien: int):
    obj = await get_loai_cam_bien_by_id(db, ma_loai_cam_bien)
    if obj:
        q = select(func.count()).select_from(CamBien).where(CamBien.loai == ma_loai_cam_bien)
        res = await db.execute(q)
        count = int(res.scalar_one())
        if count > 0:
            return False
        await db.delete(obj)
        return True
    return False
