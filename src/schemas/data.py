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
    tuoi: Optional[int]  # 0/1
    giai_doan: Optional[str]  # nảy mầm, sinh trưởng, thu hoach


class DataOut(BaseModel):
    ma_du_lieu: int
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
    tuoi: Optional[int]  # 0/1
    giai_doan: Optional[str]  # nảy mầm, sinh trưởng, thu hoach
    thoi_gian_tao: Optional[datetime]
