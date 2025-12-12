from typing import Optional
import math
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.schemas.du_lieu_du_bao import ForecastOut
from src.crud.may_bom import get_may_bom_by_id
from src.crud.du_lieu_du_bao import list_du_lieu_du_bao_for_user
from src.crud.thong_bao import create_notification

router = APIRouter()


async def _check_forecast_model_error(db: AsyncSession, ma_may_bom: int, ma_nguoi_dung, has_error: bool = False):
    """Kiểm tra nếu model dự báo lỗi ảnh hưởng đến user"""
    if has_error:
        pump = await get_may_bom_by_id(db, ma_may_bom)
        pump_name = pump.ten_may_bom if pump else f"Thiết bị {ma_may_bom}"
        await create_notification(
            db=db,
            ma_nguoi_dung=ma_nguoi_dung,
            loai="ALERT",
            muc_do="HIGH",
            tieu_de="Mô hình dự báo lỗi",
            noi_dung=f"Mô hình dự báo AI gặp lỗi khi xử lý dữ liệu cho thiết bị '{pump_name}'. Dự báo có thể không chính xác. Vui lòng chờ hệ thống xử lý lại.",
            ma_thiet_bi=ma_may_bom,
            du_lieu_lien_quan={"ma_may_bom": ma_may_bom, "error": True}
        )


@router.get("/", status_code=200)
async def list_du_bao(
    ma_may_bom: Optional[int] = Query(None),
    limit: int = Query(15, ge=-1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):

    if ma_may_bom:
        pump = await get_may_bom_by_id(db, ma_may_bom)
        if not pump:
            raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
        if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
            raise HTTPException(status_code=403, detail="Không được phép truy cập dữ liệu của máy bơm này")

    if page is not None and limit > 0:
        offset = (page - 1) * limit

    if limit is None or limit < 0:
        limit_arg = None
    else:
        limit_arg = limit

    rows, total = await list_du_lieu_du_bao_for_user(db, current_user.ma_nguoi_dung, ma_may_bom, limit_arg, offset)

    items = [ForecastOut.from_orm(r) for r in rows]

    resp_limit = limit if (limit is None or limit >= 0) else None
    page_num = (offset // limit) + 1 if (limit and limit > 0) else 1
    total_pages = math.ceil(total / limit) if (limit and limit > 0) else 1

    return {"data": items, "limit": resp_limit, "offset": offset, "page": page_num, "total_pages": total_pages, "total": total}


@router.post("/report-error", status_code=201)
async def report_forecast_error(
    ma_may_bom: int = Body(..., embed=True),
    mo_ta: str = Body(..., embed=True),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Báo cáo lỗi mô hình dự báo"""
    pump = await get_may_bom_by_id(db, ma_may_bom)
    if not pump:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép báo cáo lỗi cho máy bơm này")
    
    # Tạo cảnh báo cho user về lỗi model
    await _check_forecast_model_error(db, ma_may_bom, current_user.ma_nguoi_dung, has_error=True)
    await db.commit()
    
    return {"message": "Báo cáo lỗi mô hình dự báo thành công. Hệ thống sẽ xử lý lại."}
