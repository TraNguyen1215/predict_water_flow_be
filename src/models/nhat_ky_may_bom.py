from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from .base import Base


class NhatKyMayBom(Base):
    __tablename__ = "nhat_ky_may_bom"

    ma_nhat_ky = Column(Integer, primary_key=True)
    ma_may_bom = Column(Integer, ForeignKey("may_bom.ma_may_bom"))
    thoi_gian_bat = Column(DateTime)
    thoi_gian_tat = Column(DateTime)
    ghi_chu = Column(String)
    thoi_gian_tao = Column(DateTime, server_default=func.now())
    thoi_gian_cap_nhat = Column(DateTime, onupdate=func.now())
