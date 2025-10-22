from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class SensorCreate(BaseModel):
    ten_cam_bien: str
    mo_ta: Optional[str]
    ma_may_bom: Optional[int]
    ngay_lap_dat: Optional[date]
    loai: int
    thoi_gian_tao: Optional[datetime] = datetime.now()


class SensorOut(BaseModel):
    ma_cam_bien: int
    ten_cam_bien: str
    mo_ta: Optional[str]
    ngay_lap_dat: Optional[date]
    thoi_gian_tao: Optional[datetime]
    ma_may_bom: Optional[int]
    ten_may_bom: Optional[str]
    trang_thai: Optional[bool]
    loai: Optional[int]
    ten_loai_cam_bien: Optional[str]
