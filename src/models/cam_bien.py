from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from .base import Base


class CamBien(Base):
    __tablename__ = "cam_bien"

    ma_cam_bien = Column(Integer, primary_key=True)
    ma_nguoi_dung = Column(UUID(as_uuid=True), ForeignKey("nguoi_dung.ma_nguoi_dung"))
    ten_cam_bien = Column(String)
    mo_ta = Column(String)
    ngay_lap_dat = Column(Date)
    ma_may_bom = Column(Integer, ForeignKey("may_bom.ma_may_bom"))
    loai = Column(Integer, ForeignKey("loai_cam_bien.ma_loai_cam_bien"))
    trang_thai = Column(Boolean, default=True)
    thoi_gian_tao = Column(DateTime, server_default=func.now())
    thoi_gian_cap_nhat = Column(DateTime, onupdate=func.now())
