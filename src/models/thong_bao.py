from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from .base import Base


class ThongBao(Base):
    __tablename__ = "thong_bao"

    ma_thong_bao = Column(Integer, primary_key=True, autoincrement=True)
    ma_nguoi_dung = Column(UUID(as_uuid=True), nullable=True)
    ma_thiet_bi = Column(Integer, nullable=True)
    loai = Column(String, nullable=False)  # ALERT, INFO, WARNING, DEVICE, FORECAST
    muc_do = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    tieu_de = Column(String, nullable=False)
    noi_dung = Column(Text, nullable=False)
    da_xem = Column(Boolean, default=False)
    thoi_gian_tao = Column(DateTime, server_default=func.now())
    thoi_gian_cap_nhat = Column(DateTime, onupdate=func.now())
    du_lieu_lien_quan = Column(JSON, nullable=True)
