from pydantic import BaseModel, Field, field_validator, UUID4
from typing import Optional
from datetime import date, datetime


class SensorCreate(BaseModel):
    ten_cam_bien: str
    mo_ta: Optional[str] = None
    ma_may_bom: Optional[int] = None
    ngay_lap_dat: Optional[date] = None
    loai: int
    ma_nguoi_dung: Optional[UUID4] = None

    @field_validator('ma_may_bom', 'ngay_lap_dat', 'ma_nguoi_dung', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v


class SensorUpdate(BaseModel):
    ten_cam_bien: Optional[str] = None
    mo_ta: Optional[str] = None
    ma_may_bom: Optional[int] = None
    ngay_lap_dat: Optional[date] = None
    loai: Optional[int] = None
    trang_thai: Optional[bool] = None
    ma_nguoi_dung: Optional[UUID4] = None

    @field_validator('ma_may_bom', 'ngay_lap_dat', 'ma_nguoi_dung', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v


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
