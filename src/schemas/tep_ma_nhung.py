from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TepMaNhungCreate(BaseModel):
    ten_tep: str
    phien_ban: Optional[str] = None
    mo_ta: Optional[str] = None
    url: Optional[str] = None


class TepMaNhungUpdate(BaseModel):
    ten_tep: Optional[str] = None
    phien_ban: Optional[str] = None
    mo_ta: Optional[str] = None
    url: Optional[str] = None


class TepMaNhungOut(BaseModel):
    ma_tep_ma_nhung: int
    ten_tep: Optional[str] = None
    phien_ban: Optional[str] = None
    mo_ta: Optional[str] = None
    url: Optional[str] = None
    thoi_gian_tao: Optional[datetime] = None
    thoi_gian_cap_nhat: Optional[datetime] = None
