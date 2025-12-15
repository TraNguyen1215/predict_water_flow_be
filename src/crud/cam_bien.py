from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime
from src.schemas.sensor import SensorCreate, SensorUpdate
from src.models.cam_bien import CamBien
from src.models.may_bom import MayBom
from src.models.loai_cam_bien import LoaiCamBien
from src.crud import thong_bao as crud_thong_bao


async def create_cam_bien(db: AsyncSession, ma_nd, payload: SensorCreate) -> CamBien:
    obj = CamBien(ma_nguoi_dung=ma_nd, ten_cam_bien=payload.ten_cam_bien, mo_ta=payload.mo_ta, ngay_lap_dat=payload.ngay_lap_dat, ma_may_bom=payload.ma_may_bom, loai=payload.loai)
    db.add(obj)
    await db.flush()
    
    # Tạo thông báo
    await crud_thong_bao.create_notification(
        db,
        ma_nd,
        loai="DEVICE",
        muc_do="INFO",
        tieu_de=f"Cảm biến '{payload.ten_cam_bien}' đã được tạo",
        noi_dung=f"Cảm biến '{payload.ten_cam_bien}' đã được tạo thành công. {payload.mo_ta or ''}",
        ma_thiet_bi=payload.ma_may_bom,
        du_lieu_lien_quan={"ten_cam_bien": payload.ten_cam_bien, "loai": payload.loai},
    )
    
    return obj


async def list_cam_bien_for_user(db: AsyncSession, ma_nd, limit: int, offset: int):
    q = (
        select(
            CamBien.ma_cam_bien.label("ma_cam_bien"),
            CamBien.ten_cam_bien.label("ten_cam_bien"),
            CamBien.mo_ta.label("mo_ta"),
            CamBien.ngay_lap_dat.label("ngay_lap_dat"),
            CamBien.thoi_gian_tao.label("thoi_gian_tao"),
            CamBien.ma_may_bom.label("ma_may_bom"),
            MayBom.ten_may_bom.label("ten_may_bom"),
            CamBien.trang_thai.label("trang_thai"),
            CamBien.loai.label("loai"),
            LoaiCamBien.ten_loai_cam_bien.label("ten_loai_cam_bien"),
        )
        .join(MayBom, CamBien.ma_may_bom == MayBom.ma_may_bom, isouter=True)
        .join(LoaiCamBien, CamBien.loai == LoaiCamBien.ma_loai_cam_bien)
        .where(CamBien.ma_nguoi_dung == ma_nd)
        .order_by(CamBien.thoi_gian_tao.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(q)
    items = res.mappings().all()

    count_q = select(func.count()).select_from(CamBien).where(CamBien.ma_nguoi_dung == ma_nd)
    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())
    return items, total


async def get_cam_bien_with_names_by_id(db: AsyncSession, ma_cam_bien: int):
    """Return a single row (labeled) with pump and type names for endpoints that need them."""
    q = (
        select(
            CamBien.ma_cam_bien.label("ma_cam_bien"),
            CamBien.ten_cam_bien.label("ten_cam_bien"),
            CamBien.ma_nguoi_dung.label("ma_nguoi_dung"),
            CamBien.mo_ta.label("mo_ta"),
            CamBien.ngay_lap_dat.label("ngay_lap_dat"),
            CamBien.thoi_gian_tao.label("thoi_gian_tao"),
            CamBien.ma_may_bom.label("ma_may_bom"),
            MayBom.ten_may_bom.label("ten_may_bom"),
            CamBien.trang_thai.label("trang_thai"),
            CamBien.loai.label("loai"),
            LoaiCamBien.ten_loai_cam_bien.label("ten_loai_cam_bien"),
        )
        .join(MayBom, CamBien.ma_may_bom == MayBom.ma_may_bom, isouter=True)
        .join(LoaiCamBien, CamBien.loai == LoaiCamBien.ma_loai_cam_bien)
        .where(CamBien.ma_cam_bien == ma_cam_bien)
    )
    res = await db.execute(q)
    return res.mappings().first()


async def get_cam_bien_by_id(db: AsyncSession, ma_cam_bien: int):
    q = select(CamBien).where(CamBien.ma_cam_bien == ma_cam_bien)
    res = await db.execute(q)
    return res.scalars().first()


async def update_cam_bien(db: AsyncSession, ma_cam_bien: int, payload: SensorUpdate):
    obj = await get_cam_bien_by_id(db, ma_cam_bien)
    if not obj:
        return None
    
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)

    obj.thoi_gian_cap_nhat = datetime.now()
    await db.flush()
    
    # Tạo thông báo
    await crud_thong_bao.create_notification(
        db,
        obj.ma_nguoi_dung,
        loai="DEVICE",
        muc_do="INFO",
        tieu_de=f"Cảm biến '{obj.ten_cam_bien}' đã được cập nhật",
        noi_dung=f"Cảm biến '{obj.ten_cam_bien}' đã được cập nhật thành công.",
        ma_thiet_bi=obj.ma_may_bom,
        du_lieu_lien_quan={"ten_cam_bien": obj.ten_cam_bien, "loai": obj.loai},
    )
    
    return obj


async def delete_cam_bien(db: AsyncSession, ma_cam_bien: int):
    obj = await get_cam_bien_by_id(db, ma_cam_bien)
    if obj:
        # Tạo thông báo trước khi xoá
        await crud_thong_bao.create_notification(
            db,
            obj.ma_nguoi_dung,
            loai="DEVICE",
            muc_do="INFO",
            tieu_de=f"Cảm biến '{obj.ten_cam_bien}' đã được xoá",
            noi_dung=f"Cảm biến '{obj.ten_cam_bien}' đã được xoá khỏi hệ thống.",
            ma_thiet_bi=obj.ma_may_bom,
            du_lieu_lien_quan={"ten_cam_bien": obj.ten_cam_bien},
        )
        await db.delete(obj)


async def list_all_cam_bien(db: AsyncSession, limit: int, offset: int):
    """Lấy danh sách tất cả cảm biến (dùng cho admin)"""
    q = (
        select(
            CamBien.ma_cam_bien.label("ma_cam_bien"),
            CamBien.ten_cam_bien.label("ten_cam_bien"),
            CamBien.mo_ta.label("mo_ta"),
            CamBien.ngay_lap_dat.label("ngay_lap_dat"),
            CamBien.thoi_gian_tao.label("thoi_gian_tao"),
            CamBien.ma_may_bom.label("ma_may_bom"),
            CamBien.ma_nguoi_dung.label("ma_nguoi_dung"),
            MayBom.ten_may_bom.label("ten_may_bom"),
            CamBien.trang_thai.label("trang_thai"),
            CamBien.loai.label("loai"),
            LoaiCamBien.ten_loai_cam_bien.label("ten_loai_cam_bien"),
        )
        .join(MayBom, CamBien.ma_may_bom == MayBom.ma_may_bom, isouter=True)
        .join(LoaiCamBien, CamBien.loai == LoaiCamBien.ma_loai_cam_bien)
        .order_by(CamBien.thoi_gian_tao.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(q)
    items = res.mappings().all()

    count_q = select(func.count()).select_from(CamBien)
    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())
    return items, total


async def count_cam_bien_for_user(db: AsyncSession, ma_nguoi_dung) -> int:
    """Đếm số lượng cảm biến của một người dùng"""
    q = select(func.count()).select_from(CamBien).where(CamBien.ma_nguoi_dung == ma_nguoi_dung)
    res = await db.execute(q)
    return int(res.scalar_one())
