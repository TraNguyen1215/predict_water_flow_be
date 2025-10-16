from typing import Optional
from datetime import datetime
import uuid


class User:
    """User model representing a user in the database."""
    
    def __init__(
        self,
        ma_nguoi_dung: Optional[uuid.UUID] = None,
        ten_dang_nhap: str = None,
        mat_khau: str = None,
        ho_ten: str = None,
        email: Optional[str] = None,
        sdt: Optional[str] = None,
        dia_chi: Optional[str] = None,
        trang_thai: bool = True,
        ngay_tao: Optional[datetime] = None,
        ngay_cap_nhat: Optional[datetime] = None
    ):
        self.ma_nguoi_dung = ma_nguoi_dung
        self.ten_dang_nhap = ten_dang_nhap
        self.mat_khau = mat_khau
        self.ho_ten = ho_ten
        self.email = email
        self.sdt = sdt
        self.dia_chi = dia_chi
        self.trang_thai = trang_thai
        self.ngay_tao = ngay_tao
        self.ngay_cap_nhat = ngay_cap_nhat
    
    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            "id": self.id,
            "ten_dang_nhap": self.ten_dang_nhap,
            "ho_ten": self.ho_ten,
            "email": self.email,
            "sdt": self.sdt,
            "dia_chi": self.dia_chi,
            "trang_thai": self.trang_thai,
            "ngay_tao": self.ngay_tao,
            "ngay_cap_nhat": self.ngay_cap_nhat
        }
