import uuid
from sqlalchemy import Column, DateTime, Integer, Date, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from .base import Base


class DuLieuCamBien(Base):
    __tablename__ = "du_lieu_cam_bien"

    ma_du_lieu = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ma_may_bom = Column(Integer, ForeignKey("may_bom.ma_may_bom"))
    ma_nguoi_dung = Column(UUID(as_uuid=True), ForeignKey("nguoi_dung.ma_nguoi_dung"))
    ngay = Column(Date)
    luu_luong_nuoc = Column(Float)
    do_am_dat = Column(Float)
    nhiet_do = Column(Float)
    do_am = Column(Float)
    mua = Column(Float)
    so_xung = Column(Integer)
    tong_the_tich = Column(Float)
    thoi_gian_tao = Column(DateTime, server_default=func.now())
    ghi_chu = Column(String)
