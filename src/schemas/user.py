from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from src.schemas.pump import PumpOut
from src.schemas.sensor import SensorOut


class UserPublicMinimal(BaseModel):
    ma_nguoi_dung: UUID
    ten_dang_nhap: str
    ho_ten: Optional[str] = None


class UserPublic(BaseModel):
    ma_nguoi_dung: UUID
    ten_dang_nhap: str
    ho_ten: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    dia_chi: Optional[str] = None
    avatar: Optional[str] = None
    trang_thai: Optional[bool] = None
    thoi_gian_tao: Optional[datetime] = None
    dang_nhap_lan_cuoi: Optional[datetime] = None
    quan_tri_vien: Optional[bool] = None
    may_bom: List[PumpOut] = Field(default_factory=list)
    cam_bien: List[SensorOut] = Field(default_factory=list)
    tong_may_bom: int = Field(default=0)
    tong_cam_bien: int = Field(default=0)


class UserUpdate(BaseModel):
    ho_ten: Optional[str]
    so_dien_thoai: Optional[str]
    dia_chi: Optional[str]
    quan_tri_vien: Optional[bool]
    trang_thai: Optional[bool]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    details: Optional[str]
    exp: int
    expires_at: str
