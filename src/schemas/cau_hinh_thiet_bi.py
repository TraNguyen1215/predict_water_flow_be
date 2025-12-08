from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CauHinhThietBiCreate(BaseModel):
    ma_thiet_bi: int
    do_am_toi_thieu: Optional[int] = None
    do_am_toi_da: Optional[int] = None
    nhiet_do_toi_da: Optional[float] = None
    luu_luong_toi_thieu: Optional[float] = None
    gio_bat_dau: Optional[int] = None
    gio_ket_thuc: Optional[int] = None
    tan_suat_gui_du_lieu: Optional[int] = None


class CauHinhThietBiUpdate(BaseModel):
    do_am_toi_thieu: Optional[int] = None
    do_am_toi_da: Optional[int] = None
    nhiet_do_toi_da: Optional[float] = None
    luu_luong_toi_thieu: Optional[float] = None
    gio_bat_dau: Optional[int] = None
    gio_ket_thuc: Optional[int] = None
    tan_suat_gui_du_lieu: Optional[int] = None


class CauHinhThietBiResponse(BaseModel):
    ma_cau_hinh: int
    ma_thiet_bi: int
    do_am_toi_thieu: Optional[int] = None
    do_am_toi_da: Optional[int] = None
    nhiet_do_toi_da: Optional[float] = None
    luu_luong_toi_thieu: Optional[float] = None
    gio_bat_dau: Optional[int] = None
    gio_ket_thuc: Optional[int] = None
    tan_suat_gui_du_lieu: Optional[int] = None
    thoi_gian_tao: Optional[datetime] = None
    thoi_gian_cap_nhat: Optional[datetime] = None
