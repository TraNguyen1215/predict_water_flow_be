from pydantic import BaseModel
from typing import Optional


class UserPublicMinimal(BaseModel):
    ma_nguoi_dung: str
    ten_dang_nhap: str
    ho_ten: Optional[str] = None