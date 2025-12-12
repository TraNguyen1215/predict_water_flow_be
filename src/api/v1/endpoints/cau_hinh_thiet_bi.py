from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import math
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.crud.cau_hinh_thiet_bi import (
    create_cau_hinh_thiet_bi,
    get_cau_hinh_by_id,
    get_cau_hinh_by_thiet_bi,
    list_cau_hinh,
    update_cau_hinh,
    delete_cau_hinh,
)
from src.schemas.cau_hinh_thiet_bi import (
    CauHinhThietBiCreate,
    CauHinhThietBiUpdate,
    CauHinhThietBiResponse,
)
from src.crud.may_bom import get_may_bom_by_id
from src.crud.nguoi_dung import get_all_admins, get_by_id as get_user_by_id
from src.crud.thong_bao import create_notification

router = APIRouter()


@router.post("/", status_code=201, response_model=CauHinhThietBiResponse)
async def create_cau_hinh_thiet_bi_endpoint(
    payload: CauHinhThietBiCreate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo cấu hình thiết bị mới. Chỉ quản trị viên mới có quyền."""
    # Kiểm tra quyền quản trị viên
    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới có quyền tạo cấu hình thiết bị")
    
    # Kiểm tra xem thiết bị (may_bom) có tồn tại không
    pump = await get_may_bom_by_id(db, payload.ma_thiet_bi)
    if not pump:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị (may_bom)")
    
    config = await create_cau_hinh_thiet_bi(db, payload.ma_thiet_bi, payload.dict())
    await db.commit()
    return CauHinhThietBiResponse(
        ma_cau_hinh=config.ma_cau_hinh,
        ma_thiet_bi=config.ma_thiet_bi,
        do_am_toi_thieu=config.do_am_toi_thieu,
        do_am_toi_da=config.do_am_toi_da,
        nhiet_do_toi_da=config.nhiet_do_toi_da,
        luu_luong_toi_thieu=config.luu_luong_toi_thieu,
        gio_bat_dau=config.gio_bat_dau,
        gio_ket_thuc=config.gio_ket_thuc,
        tan_suat_gui_du_lieu=config.tan_suat_gui_du_lieu,
        thoi_gian_tao=config.thoi_gian_tao,
        thoi_gian_cap_nhat=config.thoi_gian_cap_nhat,
    )


@router.get("/", status_code=200)
async def list_cau_hinh_thiet_bi_endpoint(
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """Danh sách cấu hình thiết bị."""
    if page is not None:
        offset = (page - 1) * limit

    items, total = await list_cau_hinh(db, limit, offset)
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    data = [
        CauHinhThietBiResponse(
            ma_cau_hinh=item.ma_cau_hinh,
            ma_thiet_bi=item.ma_thiet_bi,
            do_am_toi_thieu=item.do_am_toi_thieu,
            do_am_toi_da=item.do_am_toi_da,
            nhiet_do_toi_da=item.nhiet_do_toi_da,
            luu_luong_toi_thieu=item.luu_luong_toi_thieu,
            gio_bat_dau=item.gio_bat_dau,
            gio_ket_thuc=item.gio_ket_thuc,
            tan_suat_gui_du_lieu=item.tan_suat_gui_du_lieu,
            thoi_gian_tao=item.thoi_gian_tao,
            thoi_gian_cap_nhat=item.thoi_gian_cap_nhat,
        )
        for item in items
    ]
    return {
        "data": data,
        "limit": limit,
        "offset": offset,
        "page": page,
        "total_pages": total_pages,
        "total": total
    }


@router.get("/{ma_cau_hinh}", status_code=200, response_model=CauHinhThietBiResponse)
async def get_cau_hinh_thiet_bi_endpoint(
    ma_cau_hinh: int,
    db: AsyncSession = Depends(deps.get_db_session),
):
    """Lấy cấu hình thiết bị theo mã cấu hình."""
    config = await get_cau_hinh_by_id(db, ma_cau_hinh)
    if not config:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình thiết bị")
    return CauHinhThietBiResponse(
        ma_cau_hinh=config.ma_cau_hinh,
        ma_thiet_bi=config.ma_thiet_bi,
        do_am_toi_thieu=config.do_am_toi_thieu,
        do_am_toi_da=config.do_am_toi_da,
        nhiet_do_toi_da=config.nhiet_do_toi_da,
        luu_luong_toi_thieu=config.luu_luong_toi_thieu,
        gio_bat_dau=config.gio_bat_dau,
        gio_ket_thuc=config.gio_ket_thuc,
        tan_suat_gui_du_lieu=config.tan_suat_gui_du_lieu,
        thoi_gian_tao=config.thoi_gian_tao,
        thoi_gian_cap_nhat=config.thoi_gian_cap_nhat,
    )


@router.get("/thiet-bi/{ma_thiet_bi}", status_code=200, response_model=CauHinhThietBiResponse)
async def get_cau_hinh_by_thiet_bi_endpoint(
    ma_thiet_bi: int,
    db: AsyncSession = Depends(deps.get_db_session),
):
    """Lấy cấu hình thiết bị theo mã thiết bị (ma_thiet_bi)."""
    config = await get_cau_hinh_by_thiet_bi(db, ma_thiet_bi)
    if not config:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình thiết bị")
    return CauHinhThietBiResponse(
        ma_cau_hinh=config.ma_cau_hinh,
        ma_thiet_bi=config.ma_thiet_bi,
        do_am_toi_thieu=config.do_am_toi_thieu,
        do_am_toi_da=config.do_am_toi_da,
        nhiet_do_toi_da=config.nhiet_do_toi_da,
        luu_luong_toi_thieu=config.luu_luong_toi_thieu,
        gio_bat_dau=config.gio_bat_dau,
        gio_ket_thuc=config.gio_ket_thuc,
        tan_suat_gui_du_lieu=config.tan_suat_gui_du_lieu,
        thoi_gian_tao=config.thoi_gian_tao,
        thoi_gian_cap_nhat=config.thoi_gian_cap_nhat,
    )


@router.put("/{ma_cau_hinh}", status_code=200)
async def update_cau_hinh_thiet_bi_endpoint(
    ma_cau_hinh: int,
    payload: CauHinhThietBiUpdate,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật cấu hình thiết bị. Chỉ quản trị viên mới có quyền chỉnh sửa."""
    # Kiểm tra quyền quản trị viên
    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới có quyền cập nhật cấu hình thiết bị")
    
    config = await get_cau_hinh_by_id(db, ma_cau_hinh)
    if not config:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình thiết bị")
    
    await update_cau_hinh(db, ma_cau_hinh, payload.dict(exclude_unset=True))
    await db.commit()
    
    # Gửi thông báo tới tất cả admin về cập nhật cấu hình
    admins = await get_all_admins(db)
    pump = await get_may_bom_by_id(db, config.ma_thiet_bi)
    pump_name = pump.ten_may_bom if pump else f"Thiết bị {config.ma_thiet_bi}"
    
    for admin in admins:
        await create_notification(
            db=db,
            ma_nguoi_dung=admin.ma_nguoi_dung,
            loai="INFO",
            muc_do="MEDIUM",
            tieu_de="Cấu hình thiết bị đã được cập nhật",
            noi_dung=f"Cấu hình thiết bị '{pump_name}' vừa được cập nhật thành công bởi quản trị viên.",
            ma_thiet_bi=config.ma_thiet_bi,
            du_lieu_lien_quan={"ma_cau_hinh": ma_cau_hinh, "ma_thiet_bi": config.ma_thiet_bi}
        )
    
    # Gửi thông báo tới người dùng sở hữu thiết bị về cập nhật cấu hình
    if pump:
        user = await get_user_by_id(db, pump.ma_nguoi_dung)
        if user:
            await create_notification(
                db=db,
                ma_nguoi_dung=user.ma_nguoi_dung,
                loai="INFO",
                muc_do="MEDIUM",
                tieu_de="Cấu hình thiết bị được cập nhật",
                noi_dung=f"Cấu hình thiết bị '{pump_name}' của bạn đã được cập nhật bởi quản trị viên.",
                ma_thiet_bi=config.ma_thiet_bi,
                du_lieu_lien_quan={"ma_cau_hinh": ma_cau_hinh, "ma_thiet_bi": config.ma_thiet_bi}
            )
    
    await db.commit()
    return {"message": "Cập nhật cấu hình thiết bị thành công", "ma_cau_hinh": ma_cau_hinh}


@router.delete("/{ma_cau_hinh}", status_code=200)
async def delete_cau_hinh_thiet_bi_endpoint(
    ma_cau_hinh: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá cấu hình thiết bị. Chỉ quản trị viên mới có quyền xoá."""
    # Kiểm tra quyền quản trị viên
    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới có quyền xoá cấu hình thiết bị")
    
    config = await get_cau_hinh_by_id(db, ma_cau_hinh)
    if not config:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình thiết bị")
    
    await delete_cau_hinh(db, ma_cau_hinh)
    await db.commit()
    return {"message": "Xoá cấu hình thiết bị thành công", "ma_cau_hinh": ma_cau_hinh}
