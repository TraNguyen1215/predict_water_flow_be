from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any
from uuid import UUID


class ThongBaoBase(BaseModel):
    loai: str  # ALERT, INFO, WARNING, DEVICE, FORECAST
    muc_do: str  # LOW, MEDIUM, HIGH, CRITICAL
    tieu_de: str
    noi_dung: str
    da_xem: bool = False
    du_lieu_lien_quan: Optional[Any] = None


class ThongBaoCreate(ThongBaoBase):
    ma_nguoi_dung: UUID
    ma_thiet_bi: Optional[int] = None


class ThongBaoUpdate(BaseModel):
    loai: Optional[str] = None
    muc_do: Optional[str] = None
    tieu_de: Optional[str] = None
    noi_dung: Optional[str] = None
    da_xem: Optional[bool] = None
    du_lieu_lien_quan: Optional[Any] = None


class ThongBaoResponse(ThongBaoBase):
    ma_thong_bao: int
    ma_nguoi_dung: UUID
    ma_thiet_bi: Optional[int]
    thoi_gian_tao: datetime
    thoi_gian_cap_nhat: Optional[datetime]
