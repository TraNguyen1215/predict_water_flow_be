from pydantic import BaseModel, Field, field_validator, UUID4
from typing import List, Optional
from datetime import datetime
from src.schemas.sensor import SensorOut


class PumpMinimal(BaseModel):
    ma_may_bom: int
    ten_may_bom: str
    mo_ta: Optional[str] = None
    trang_thai: Optional[bool] = None
    gioi_han_thoi_gian: Optional[bool] = None


class PumpCreate(BaseModel):
    ten_may_bom: str
    mo_ta: Optional[str] = None
    che_do: Optional[int] = None
    trang_thai: Optional[bool] = True
    gioi_han_thoi_gian: Optional[bool] = True
    ma_nguoi_dung: Optional[UUID4] = None

    @field_validator('ma_nguoi_dung', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v


class PumpUpdate(BaseModel):
    ten_may_bom: Optional[str] = None
    mo_ta: Optional[str] = None
    che_do: Optional[int] = None
    trang_thai: Optional[bool] = None
    gioi_han_thoi_gian: Optional[bool] = None
    ma_nguoi_dung: Optional[UUID4] = None

    @field_validator('ma_nguoi_dung', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v



class PumpOut(BaseModel):
    ma_may_bom: int
    ten_may_bom: str = None
    mo_ta: Optional[str] = None
    che_do: Optional[int] = None
    trang_thai: Optional[bool] = None
    gioi_han_thoi_gian: Optional[bool] = None
    thoi_gian_tao: Optional[datetime] = None
    tong_cam_bien: int = Field(default=0)
    cam_bien: List[SensorOut] = Field(default_factory=list)
