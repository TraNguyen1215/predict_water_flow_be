from sqlalchemy import Column, BigInteger, DateTime, String, Date, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from .base import Base


class NhatKyGieoTrong(Base):
    __tablename__ = "nhat_ky_gieo_trong"

    ma_gieo_trong = Column(BigInteger, primary_key=True, autoincrement=True)
    ma_nguoi_dung = Column(UUID(as_uuid=True), ForeignKey("nguoi_dung.ma_nguoi_dung"), nullable=False)
    ten_cay_trong = Column(String)
    noi_dung = Column(String)
    dien_tich_trong = Column(Float)
    ngay_gieo_trong = Column(Date)
    giai_doan = Column(String)
    trang_thai = Column(Boolean, default=True)
    thoi_gian_da_gieo = Column(String)
    thoi_gian_tao = Column(DateTime(timezone=True), server_default=func.now())
    thoi_gian_cap_nhat = Column(DateTime(timezone=True), onupdate=func.now())
