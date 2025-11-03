from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PumpMinimal(BaseModel):
    ma_may_bom: int
    ten_may_bom: str
    mo_ta: Optional[str] = None
    trang_thai: Optional[bool] = None