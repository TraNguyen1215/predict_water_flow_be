from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from .base import Base


class NguoiDung(Base):
    __tablename__ = "nguoi_dung"

    ma_nguoi_dung = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ten_dang_nhap = Column(String, unique=True, nullable=False)
    mat_khau_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    ho_ten = Column(String)
    so_dien_thoai = Column(String)
    dia_chi = Column(String)
    trang_thai = Column(Boolean, default=True)
    dang_nhap_lan_cuoi = Column(DateTime)
    thoi_gian_tao = Column(DateTime, server_default=func.now())
    thoi_gian_cap_nhat = Column(DateTime, onupdate=func.now())
    quan_tri_vien = Column(Boolean, default=False)
