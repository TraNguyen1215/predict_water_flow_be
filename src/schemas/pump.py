from pydantic import BaseModel, Field
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
