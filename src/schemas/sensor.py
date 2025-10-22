from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class SensorCreate(BaseModel):
    ten_cam_bien: str
    mo_ta: Optional[str] = None
    ma_may_bom: Optional[int] = None
    ngay_lap_dat: Optional[date] = None
    loai: int


class SensorOut(BaseModel):
    ma_cam_bien: int
    ten_cam_bien: str
    mo_ta: Optional[str] = None
    ngay_lap_dat: Optional[date] = None
    thoi_gian_tao: Optional[datetime] = Field(default=None)
    ma_may_bom: Optional[int] = None
    ten_may_bom: Optional[str] = None
    trang_thai: Optional[bool] = None
    loai: Optional[int] = None
    ten_loai_cam_bien: Optional[str] = None
