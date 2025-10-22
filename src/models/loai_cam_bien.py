from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .base import Base


class LoaiCamBien(Base):
    __tablename__ = "loai_cam_bien"

    ma_loai_cam_bien = Column(Integer, primary_key=True)
    ten_loai_cam_bien = Column(String)
    thoi_gian_tao = Column(DateTime, server_default=func.now())
    thoi_gian_cap_nhat = Column(DateTime, onupdate=func.now())
