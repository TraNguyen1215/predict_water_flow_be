from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class NhatKyGieoTrongCreate(BaseModel):
    ma_nguoi_dung: Optional[UUID]
    ten_cay_trong: Optional[str]
    noi_dung: Optional[str]
    dien_tich_trong: Optional[float]
    ngay_gieo_trong: Optional[date]
    giai_doan: Optional[str]
    thoi_gian_da_gieo: Optional[str]
    trang_thai: Optional[bool] = True


class NhatKyGieoTrongOut(BaseModel):
    ma_gieo_trong: int
    ma_nguoi_dung: UUID
    ten_cay_trong: Optional[str]
    noi_dung: Optional[str]
    dien_tich_trong: Optional[float]
    ngay_gieo_trong: Optional[date]
    giai_doan: Optional[str]
    thoi_gian_da_gieo: Optional[str]
    trang_thai: Optional[bool]
    thoi_gian_tao: Optional[datetime]
    thoi_gian_cap_nhat: Optional[datetime]
