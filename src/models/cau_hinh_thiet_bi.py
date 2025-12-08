from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, BigInteger, Float
from sqlalchemy.sql import func
from .base import Base


class CauHinhThietBi(Base):
    __tablename__ = "cau_hinh_thiet_bi"

    ma_cau_hinh = Column(Integer, primary_key=True)
    ma_thiet_bi = Column(Integer, ForeignKey("may_bom.ma_may_bom"), nullable=False)
    do_am_toi_thieu = Column(BigInteger)
    do_am_toi_da = Column(BigInteger)
    nhiet_do_toi_da = Column(Float)
    luu_luong_toi_thieu = Column(Float)
    gio_bat_dau = Column(BigInteger)
    gio_ket_thuc = Column(BigInteger)
    tan_suat_gui_du_lieu = Column(BigInteger)
    thoi_gian_tao = Column(DateTime, server_default=func.now())
    thoi_gian_cap_nhat = Column(DateTime, onupdate=func.now())
