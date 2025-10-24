import uuid
from sqlalchemy import Column, DateTime, Float, String, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from .base import Base


class DuLieuDuBao(Base):
    __tablename__ = "du_lieu_du_bao"

    ma_du_bao = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mo_hinh = Column(String)
    thoi_diem_du_bao = Column(DateTime(timezone=True))
    luu_luong_du_bao = Column(Float, default=0)
    luu_luong_thuc_te = Column(Float, default=0)
    do_tin_cay = Column(Float, default=0)
    thoi_gian_tao = Column(DateTime, server_default=func.now())
    ma_nguoi_dung = Column(PG_UUID(as_uuid=True), ForeignKey("nguoi_dung.ma_nguoi_dung"), nullable=False)
    ma_may_bom = Column(Integer, ForeignKey("may_bom.ma_may_bom"), nullable=False)
