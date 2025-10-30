from datetime import date, datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, delete, func, or_, select, update
from src.models.cam_bien import CamBien
from src.models.loai_cam_bien import LoaiCamBien
from src.models.may_bom import MayBom
from src.models.nguoi_dung import NguoiDung
from src.models.du_lieu_cam_bien import DuLieuCamBien
from src.models.du_lieu_du_bao import DuLieuDuBao
from src.models.nhat_ky_may_bom import NhatKyMayBom
from uuid import UUID


async def get_by_username(db: AsyncSession, ten_dang_nhap: str) -> Optional[NguoiDung]:
    q = select(NguoiDung).where(NguoiDung.ten_dang_nhap == ten_dang_nhap)
    res = await db.execute(q)
    return res.scalars().first()


async def get_by_id(db: AsyncSession, ma_nguoi_dung: UUID) -> Optional[NguoiDung]:
    q = select(NguoiDung).where(NguoiDung.ma_nguoi_dung == ma_nguoi_dung)
    res = await db.execute(q)
    return res.scalars().first()


async def create_user(db: AsyncSession, ten_dang_nhap: str, mat_khau_hash: str, salt: str, ho_ten: Optional[str] = None) -> NguoiDung:
    user = NguoiDung(ten_dang_nhap=ten_dang_nhap, mat_khau_hash=mat_khau_hash, salt=salt, ho_ten=ho_ten, so_dien_thoai=ten_dang_nhap)
    db.add(user)
    await db.flush()
    return user


async def update_password(db: AsyncSession, ma_nguoi_dung: UUID, mat_khau_hash: str, salt: str):
    await db.execute(
        update(NguoiDung)
        .where(NguoiDung.ma_nguoi_dung == ma_nguoi_dung)
        .values(mat_khau_hash=mat_khau_hash, salt=salt)
    )


async def update_avatar(db: AsyncSession, ma_nguoi_dung: UUID, avatar: str):
    await db.execute(
        update(NguoiDung)
        .where(NguoiDung.ma_nguoi_dung == ma_nguoi_dung)
        .values(avatar=avatar)
    )


async def delete_user(db: AsyncSession, ma_nguoi_dung: UUID):
    await db.execute(delete(NguoiDung).where(NguoiDung.ma_nguoi_dung == ma_nguoi_dung))


async def verify_user_by_pump_and_date(db: AsyncSession, ten_dang_nhap: str, ten_may_bom: str, ngay_tuoi_gan_nhat: date) -> Optional[NguoiDung]:
    """Return the most recent NguoiDung matching the username, pump name and a matching nhat_ky_may_bom.ngay value.

    This replicates the SQL join:
        nguoi_dung nd
        JOIN may_bom mb ON nd.ma_nguoi_dung = mb.ma_nguoi_dung
        JOIN nhat_ky_may_bom nk ON nk.ma_may_bom = mb.ma_may_bom
    with ordering on nk.thoi_gian_tao DESC and LIMIT 1.
    """
    from sqlalchemy import select
    from src.models.may_bom import MayBom
    from src.models.nhat_ky_may_bom import NhatKyMayBom
    
    q = (
        select(NguoiDung)
        .join(MayBom, NguoiDung.ma_nguoi_dung == MayBom.ma_nguoi_dung)
        .join(NhatKyMayBom, NhatKyMayBom.ma_may_bom == MayBom.ma_may_bom)
        .where(NguoiDung.ten_dang_nhap == ten_dang_nhap)
        .where(MayBom.ten_may_bom == ten_may_bom)
        .where((func.date(NhatKyMayBom.thoi_gian_bat) == ngay_tuoi_gan_nhat))
        .order_by(NhatKyMayBom.thoi_gian_tao.desc())
        .limit(1)
    )
    res = await db.execute(q)
    return res.scalars().first()


async def _apply_user_inactivity_policy(db: AsyncSession):
    """Mark inactive users and purge their related data after extended inactivity."""

    now = datetime.utcnow()
    inactive_date = (now - timedelta(days=30)).date()
    cleanup_date = (now - timedelta(days=90)).date()

    inactive_condition = or_(
        and_(
            NguoiDung.dang_nhap_lan_cuoi.isnot(None),
            func.date(NguoiDung.dang_nhap_lan_cuoi) <= inactive_date,
        ),
        and_(
            NguoiDung.dang_nhap_lan_cuoi.is_(None),
            func.date(NguoiDung.thoi_gian_tao) <= inactive_date,
        ),
    )

    await db.execute(
        update(NguoiDung)
        .where(inactive_condition)
        .values(trang_thai=False)
    )

    await db.execute(
        update(NguoiDung)
        .where(NguoiDung.dang_nhap_lan_cuoi.isnot(None))
        .where(func.date(NguoiDung.dang_nhap_lan_cuoi) > inactive_date)
        .values(trang_thai=True)
    )

    cleanup_condition = or_(
        and_(
            NguoiDung.dang_nhap_lan_cuoi.isnot(None),
            func.date(NguoiDung.dang_nhap_lan_cuoi) <= cleanup_date,
        ),
        and_(
            NguoiDung.dang_nhap_lan_cuoi.is_(None),
            func.date(NguoiDung.thoi_gian_tao) <= cleanup_date,
        ),
    )

    cleanup_res = await db.execute(select(NguoiDung.ma_nguoi_dung).where(cleanup_condition))
    cleanup_user_ids = [row[0] for row in cleanup_res.all()]

    if cleanup_user_ids:
        pump_res = await db.execute(
            select(MayBom.ma_may_bom).where(MayBom.ma_nguoi_dung.in_(cleanup_user_ids))
        )
        pump_ids = [row[0] for row in pump_res.all()]

        if pump_ids:
            await db.execute(delete(NhatKyMayBom).where(NhatKyMayBom.ma_may_bom.in_(pump_ids)))
            await db.execute(delete(DuLieuCamBien).where(DuLieuCamBien.ma_may_bom.in_(pump_ids)))
            await db.execute(delete(DuLieuDuBao).where(DuLieuDuBao.ma_may_bom.in_(pump_ids)))

        await db.execute(delete(DuLieuCamBien).where(DuLieuCamBien.ma_nguoi_dung.in_(cleanup_user_ids)))
        await db.execute(delete(DuLieuDuBao).where(DuLieuDuBao.ma_nguoi_dung.in_(cleanup_user_ids)))
        await db.execute(delete(CamBien).where(CamBien.ma_nguoi_dung.in_(cleanup_user_ids)))
        await db.execute(delete(MayBom).where(MayBom.ma_nguoi_dung.in_(cleanup_user_ids)))

    await db.commit()


async def list_users(db: AsyncSession, limit: int = 50, offset: int = 0):
    await _apply_user_inactivity_policy(db)

    q = select(NguoiDung).order_by(NguoiDung.thoi_gian_tao.desc()).limit(limit).offset(offset)
    res = await db.execute(q)
    items = res.scalars().all()

    user_ids = [user.ma_nguoi_dung for user in items]
    pumps_by_user: Dict[UUID, List[dict]] = defaultdict(list)
    sensors_by_user: Dict[UUID, List[dict]] = defaultdict(list)
    pump_counts: Dict[UUID, int] = defaultdict(int)
    sensor_counts: Dict[UUID, int] = defaultdict(int)
    pump_lookup: Dict[int, dict] = {}
    sensor_counts_per_pump: Dict[int, int] = defaultdict(int)

    if user_ids:
        pump_q = (
            select(
                MayBom.ma_nguoi_dung.label("ma_nguoi_dung"),
                MayBom.ma_may_bom.label("ma_may_bom"),
                MayBom.ten_may_bom.label("ten_may_bom"),
                MayBom.mo_ta.label("mo_ta"),
                MayBom.ma_iot_lk.label("ma_iot_lk"),
                MayBom.che_do.label("che_do"),
                MayBom.trang_thai.label("trang_thai"),
                MayBom.thoi_gian_tao.label("thoi_gian_tao"),
            )
            .where(MayBom.ma_nguoi_dung.in_(user_ids))
        )
        pump_res = await db.execute(pump_q)
        for row in pump_res.mappings():
            pump_dict = dict(row)
            pump_dict["cam_bien"] = []
            pump_dict["tong_cam_bien"] = 0
            pumps_by_user[row["ma_nguoi_dung"]].append(pump_dict)
            pump_lookup[row["ma_may_bom"]] = pump_dict
            pump_counts[row["ma_nguoi_dung"]] += 1
            sensor_counts_per_pump[row["ma_may_bom"]] = 0

        sensor_q = (
            select(
                CamBien.ma_nguoi_dung.label("ma_nguoi_dung"),
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
            .join(LoaiCamBien, CamBien.loai == LoaiCamBien.ma_loai_cam_bien, isouter=True)
            .where(CamBien.ma_nguoi_dung.in_(user_ids))
        )
        sensor_res = await db.execute(sensor_q)
        for row in sensor_res.mappings():
            sensor_dict = dict(row)
            user_id = row["ma_nguoi_dung"]
            sensors_by_user[user_id].append(sensor_dict)
            sensor_counts[user_id] += 1

            pump_id = row["ma_may_bom"]
            if pump_id is not None and pump_id in pump_lookup:
                pump_lookup[pump_id]["cam_bien"].append(sensor_dict)
                sensor_counts_per_pump[pump_id] += 1
                pump_lookup[pump_id]["tong_cam_bien"] = sensor_counts_per_pump[pump_id]

    count_q = select(func.count()).select_from(NguoiDung)
    count_res = await db.execute(count_q)
    total = int(count_res.scalar_one())
    return (
        items,
        total,
        {key: value for key, value in pumps_by_user.items()},
        {key: value for key, value in sensors_by_user.items()},
        {key: value for key, value in pump_counts.items()},
        {key: value for key, value in sensor_counts.items()},
    )
