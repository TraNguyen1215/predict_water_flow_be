from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class NhatKyCreate(BaseModel):
    ma_may_bom: int
    thoi_gian_bat: Optional[datetime]
    thoi_gian_tat: Optional[datetime]
    ghi_chu: Optional[str]
    thoi_gian_tao: datetime = datetime.now()


class NhatKyOut(BaseModel):
    ma_nhat_ky: int
    ma_may_bom: int
    thoi_gian_bat: Optional[datetime]
    thoi_gian_tat: Optional[datetime]
    ghi_chu: Optional[str]
    thoi_gian_tao: Optional[datetime]
