from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ForecastCreate(BaseModel):
    mo_hinh: Optional[str]
    thoi_diem_du_bao: Optional[datetime]
    luu_luong_du_bao: Optional[float] = 0
    luu_luong_thuc_te: Optional[float] = 0
    do_tin_cay: Optional[float] = 0
    ma_may_bom: int


class ForecastOut(BaseModel):
    ma_du_bao: UUID
    mo_hinh: Optional[str]
    thoi_diem_du_bao: Optional[datetime]
    luu_luong_du_bao: Optional[float] = 0
    luu_luong_thuc_te: Optional[float] = 0
    do_tin_cay: Optional[float] = 0
    thoi_gian_tao: Optional[datetime]
    ma_nguoi_dung: UUID
    ma_may_bom: int

    class Config:
        orm_mode = True
