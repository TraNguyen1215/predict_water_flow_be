from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserPublic(BaseModel):
    ma_nguoi_dung: UUID
    ho_ten: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    dia_chi: Optional[str] = None
    avatar: Optional[str] = None
    trang_thai: Optional[bool] = None
    thoi_gian_tao: Optional[datetime] = None
    dang_nhap_lan_cuoi: Optional[datetime] = None
    quan_tri_vien: Optional[bool] = None


class UserUpdate(BaseModel):
    ho_ten: Optional[str]
    so_dien_thoai: Optional[str]
    dia_chi: Optional[str]
    quan_tri_vien: Optional[bool]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    details: Optional[str]
    exp: int
    expires_at: str
