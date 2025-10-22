from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base
from sqlalchemy import ForeignKey


class MayBom(Base):
    __tablename__ = "may_bom"

    ma_may_bom = Column(Integer, primary_key=True)
    ten_may_bom = Column(String)
    mo_ta = Column(String)
    ma_iot_lk = Column(String)
    che_do = Column(BigInteger)
    trang_thai = Column(Boolean, default=True)
    ma_nguoi_dung = Column(UUID(as_uuid=True), ForeignKey("nguoi_dung.ma_nguoi_dung"))
    thoi_gian_tao = Column(DateTime, server_default=func.now())
    thoi_gian_cap_nhat = Column(DateTime, onupdate=func.now())
