from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func
from .base import Base


class MoHinhDuBao(Base):
    __tablename__ = "mo_hinh_du_bao"

    ma_mo_hinh = Column(Integer, primary_key=True, autoincrement=True)
    ten_mo_hinh = Column(String, nullable=False)
    phien_ban = Column(String)
    thoi_gian_tao = Column(DateTime, server_default=func.now())
    thoi_gian_cap_nhat = Column(DateTime, onupdate=func.now())
    trang_thai = Column(Boolean, default=True)
