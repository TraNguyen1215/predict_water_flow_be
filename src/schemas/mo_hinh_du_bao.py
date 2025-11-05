from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MoHinhDuBaoCreate(BaseModel):
    ten_mo_hinh: str
    phien_ban: Optional[str] = None
    trang_thai: Optional[bool] = True


class MoHinhDuBaoUpdate(BaseModel):
    ten_mo_hinh: Optional[str] = None
    phien_ban: Optional[str] = None
    trang_thai: Optional[bool] = None
    thoi_gian_cap_nhat: Optional[datetime] = datetime.now()


class MoHinhDuBaoOut(BaseModel):
    ma_mo_hinh: int
    ten_mo_hinh: Optional[str] = None
    phien_ban: Optional[str] = None
    thoi_gian_tao: Optional[datetime] = None
    thoi_gian_cap_nhat: Optional[datetime] = None
    trang_thai: Optional[bool] = None
