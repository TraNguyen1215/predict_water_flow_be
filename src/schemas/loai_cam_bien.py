from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoaiCamBienCreate(BaseModel):
    ten_loai_cam_bien: str

class LoaiCamBienOut(BaseModel):
    ma_loai_cam_bien: int
    ten_loai_cam_bien: str
    thoi_gian_tao: Optional[datetime]
    thoi_gian_cap_nhat: Optional[datetime]
