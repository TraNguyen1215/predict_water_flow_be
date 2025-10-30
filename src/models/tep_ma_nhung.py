from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .base import Base


class TepMaNhung(Base):
    __tablename__ = "tep_ma_nhung"

    ma_tep_ma_nhung = Column(Integer, primary_key=True, autoincrement=True)
    ten_tep = Column(String, nullable=False)
    phien_ban = Column(String)
    mo_ta = Column(String)
    thoi_gian_tao = Column(DateTime, server_default=func.now())
    thoi_gian_cap_nhat = Column(DateTime, onupdate=func.now())
