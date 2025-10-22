from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class DataCreate(BaseModel):
    ma_may_bom: int
    ngay: date
    luu_luong_nuoc: Optional[float]
    do_am_dat: Optional[float]
    nhiet_do: Optional[float]
    do_am: Optional[float]
    mua: Optional[bool]
    so_xung: Optional[float]
    tong_the_tich: Optional[float]
    ghi_chu: Optional[str]
    thoi_gian_tao: Optional[datetime] = datetime.now()


class DataOut(BaseModel):
    ma_du_lieu: UUID
    ma_may_bom: int
    ma_nguoi_dung: Optional[UUID]
    ngay: date
    luu_luong_nuoc: Optional[float]
    do_am_dat: Optional[float]
    nhiet_do: Optional[float]
    do_am: Optional[float]
    mua: Optional[bool]
    so_xung: Optional[float]
    tong_the_tich: Optional[float]
    thoi_gian_tao: Optional[datetime]
    ghi_chu: Optional[str]
