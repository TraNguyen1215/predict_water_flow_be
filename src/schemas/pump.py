from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PumpCreate(BaseModel):
    ten_may_bom: str
    mo_ta: Optional[str]
    ma_iot_lk: Optional[str]
    che_do: Optional[int]
    trang_thai: Optional[bool] = True


class PumpOut(BaseModel):
    ma_may_bom: int
    ten_may_bom: str
    mo_ta: Optional[str]
    ma_iot_lk: Optional[str]
    che_do: Optional[int]
    trang_thai: Optional[bool]
    thoi_gian_tao: Optional[datetime]
