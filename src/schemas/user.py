from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema."""
    ten_dang_nhap: str = Field(..., min_length=3, max_length=50, description="Tên đăng nhập")
    ho_ten: str = Field(..., min_length=2, max_length=100, description="Họ và tên")
    email: Optional[EmailStr] = Field(None, description="Email")
    sdt: Optional[str] = Field(None, max_length=15, description="Số điện thoại")
    dia_chi: Optional[str] = Field(None, max_length=255, description="Địa chỉ")


class UserCreate(UserBase):
    """Schema for creating a user."""
    mat_khau: str = Field(..., min_length=6, max_length=100, description="Mật khẩu")
    
    @validator('mat_khau')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Mật khẩu phải có ít nhất 6 ký tự')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    ten_dang_nhap: str = Field(..., description="Tên đăng nhập")
    mat_khau: str = Field(..., description="Mật khẩu")


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    ho_ten: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    sdt: Optional[str] = Field(None, max_length=15)
    dia_chi: Optional[str] = Field(None, max_length=255)
    mat_khau: Optional[str] = Field(None, min_length=6, max_length=100)


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    trang_thai: bool
    ngay_tao: Optional[datetime] = None
    ngay_cap_nhat: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data."""
    user_id: Optional[int] = None
    ten_dang_nhap: Optional[str] = None
