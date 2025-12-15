import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from src.schemas.pump import PumpCreate, PumpUpdate
from typing import Optional
from src.models.may_bom import MayBom
from src.models.nguoi_dung import NguoiDung
from src.models.cam_bien import CamBien
from src.models.loai_cam_bien import LoaiCamBien
from src.models.thong_bao import ThongBao
from src.models.nhat_ky_may_bom import NhatKyMayBom
from src.models.cau_hinh_thiet_bi import CauHinhThietBi
from src.crud import thong_bao as crud_thong_bao


async def create_may_bom(db: AsyncSession, ma_nd: uuid.UUID, payload: PumpCreate) -> MayBom:
    obj = MayBom(
        ten_may_bom=payload.ten_may_bom,
        mo_ta=payload.mo_ta,
        che_do=payload.che_do,
        trang_thai=payload.trang_thai,
        gioi_han_thoi_gian=payload.gioi_han_thoi_gian,
        ma_nguoi_dung=ma_nd,
    )
    db.add(obj)
    await db.flush()
    
    # Tạo thông báo
    await crud_thong_bao.create_notification(
        db,
        ma_nd,
        loai="DEVICE",
        muc_do="INFO",
        tieu_de=f"Máy bơm '{payload.ten_may_bom}' đã được tạo",
        noi_dung=f"Máy bơm '{payload.ten_may_bom}' đã được tạo thành công. {payload.mo_ta or ''}",
        ma_thiet_bi=None,
        du_lieu_lien_quan={"ten_may_bom": payload.ten_may_bom},
    )
    
    return obj


async def list_may_bom_for_user(db: AsyncSession, ma_nd, limit: int, offset: int):
    q = select(MayBom).where(MayBom.ma_nguoi_dung == ma_nd).order_by(MayBom.thoi_gian_tao.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    items = res.scalars().all()

    count_q = select(func.count()).select_from(MayBom).where(MayBom.ma_nguoi_dung == ma_nd)
    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())
    return items, total


async def get_may_bom_by_id(db: AsyncSession, ma_may_bom: int):
    q = select(MayBom).where(MayBom.ma_may_bom == ma_may_bom)
    res = await db.execute(q)
    return res.scalars().first()


async def get_may_bom_with_sensors(db: AsyncSession, ma_may_bom: int):
    """Return pump object and its sensors (as mapping list) and sensor count."""
    pump = await get_may_bom_by_id(db, ma_may_bom)
    if not pump:
        return None

    q = (
        select(
            CamBien.ma_cam_bien.label("ma_cam_bien"),
            CamBien.ten_cam_bien.label("ten_cam_bien"),
            CamBien.mo_ta.label("mo_ta"),
            CamBien.ngay_lap_dat.label("ngay_lap_dat"),
            CamBien.thoi_gian_tao.label("thoi_gian_tao"),
            CamBien.ma_may_bom.label("ma_may_bom"),
            CamBien.trang_thai.label("trang_thai"),
            CamBien.loai.label("loai"),
            LoaiCamBien.ten_loai_cam_bien.label("ten_loai_cam_bien"),
        )
        .join(LoaiCamBien, CamBien.loai == LoaiCamBien.ma_loai_cam_bien, isouter=True)
        .where(CamBien.ma_may_bom == ma_may_bom)
        .order_by(CamBien.thoi_gian_tao.desc())
    )

    res = await db.execute(q)
    sensors = [dict(r) for r in res.mappings().all()]
    return pump, sensors, len(sensors)

async def get_may_bom_by_name_and_user(db: AsyncSession, ten_may_bom: str, ma_nguoi_dung: uuid.UUID):
    q = select(MayBom).where(
        func.lower(func.trim(MayBom.ten_may_bom)) == ten_may_bom.lower().strip(),
        MayBom.ma_nguoi_dung == ma_nguoi_dung,
    )
    res = await db.execute(q)
    return res.scalars().first()


async def update_may_bom(db: AsyncSession, ma_may_bom: int, payload: PumpUpdate):
    obj = await get_may_bom_by_id(db, ma_may_bom)
    if not obj:
        return None
    
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
    obj.trang_thai = payload.trang_thai
    obj.gioi_han_thoi_gian = payload.gioi_han_thoi_gian
    await db.flush()
    
    # Tạo thông báo
    await crud_thong_bao.create_notification(
        db,
        obj.ma_nguoi_dung,
        loai="DEVICE",
        muc_do="INFO",
        tieu_de=f"Máy bơm '{payload.ten_may_bom}' đã được cập nhật",
        noi_dung=f"Máy bơm '{payload.ten_may_bom}' đã được cập nhật thành công.",
        ma_thiet_bi=ma_may_bom,
        du_lieu_lien_quan={"ten_may_bom": payload.ten_may_bom},
    )
    
    return obj


async def delete_may_bom(db: AsyncSession, ma_may_bom: int):
    obj = await get_may_bom_by_id(db, ma_may_bom)
    if obj:
        # Xóa tất cả thông báo liên quan đến máy bơm này trước
        delete_thong_bao_q = delete(ThongBao).where(ThongBao.ma_thiet_bi == ma_may_bom)
        await db.execute(delete_thong_bao_q)
        
        # Xóa nhật ký máy bơm
        delete_nhat_ky_q = delete(NhatKyMayBom).where(NhatKyMayBom.ma_may_bom == ma_may_bom)
        await db.execute(delete_nhat_ky_q)

        # Xóa cấu hình thiết bị
        delete_cau_hinh_q = delete(CauHinhThietBi).where(CauHinhThietBi.ma_thiet_bi == ma_may_bom)
        await db.execute(delete_cau_hinh_q)
        
        # Xóa tất cả cảm biến của máy bơm này
        delete_cam_bien_q = delete(CamBien).where(CamBien.ma_may_bom == ma_may_bom)
        await db.execute(delete_cam_bien_q)
        
        # Xóa dữ liệu cảm biến liên quan
        from src.models.du_lieu_cam_bien import DuLieuCamBien
        delete_du_lieu_q = delete(DuLieuCamBien).where(DuLieuCamBien.ma_may_bom == ma_may_bom)
        await db.execute(delete_du_lieu_q)
        
        # Tạo thông báo trước khi xoá (không set ma_thiet_bi để tránh foreign key constraint)
        await crud_thong_bao.create_notification(
            db,
            obj.ma_nguoi_dung,
            loai="DEVICE",
            muc_do="INFO",
            tieu_de=f"Máy bơm '{obj.ten_may_bom}' đã được xoá",
            noi_dung=f"Máy bơm '{obj.ten_may_bom}' đã được xoá khỏi hệ thống.",
            du_lieu_lien_quan={"ten_may_bom": obj.ten_may_bom},
        )
        await db.delete(obj)


async def list_all_may_bom(db: AsyncSession, limit: int, offset: int):
    """Lấy danh sách tất cả máy bơm (dùng cho admin)"""
    q = select(MayBom).order_by(MayBom.thoi_gian_tao.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    items = res.scalars().all()

    count_q = select(func.count()).select_from(MayBom)
    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())
    return items, total


async def count_may_bom_for_user(db: AsyncSession, ma_nguoi_dung: uuid.UUID) -> int:
    """Đếm số lượng máy bơm của một người dùng"""
    q = select(func.count()).select_from(MayBom).where(MayBom.ma_nguoi_dung == ma_nguoi_dung)
    res = await db.execute(q)
    return int(res.scalar_one())
