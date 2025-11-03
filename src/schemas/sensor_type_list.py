from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from src.schemas.user import UserPublicMinimal
from src.schemas.pump import PumpMinimal


class SensorInType(BaseModel):
    ma_cam_bien: int
    ten_cam_bien: str
    mo_ta: Optional[str] = None
    ngay_lap_dat: Optional[datetime] = None
    thoi_gian_tao: Optional[datetime] = None
    trang_thai: Optional[bool] = None
    may_bom: Optional[PumpMinimal] = None
    nguoi_dung: Optional[UserPublicMinimal] = None


class SensorTypeWithSensors(BaseModel):
    ma_loai_cam_bien: int
    ten_loai_cam_bien: str
    thoi_gian_tao: Optional[datetime] = None
    thoi_gian_cap_nhat: Optional[datetime] = None
    tong_cam_bien: int = Field(default=0)
    cam_bien: List[SensorInType] = Field(default_factory=list)
