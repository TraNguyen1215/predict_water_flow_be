from typing import Optional
import math
import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import select
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.schemas.du_lieu_du_bao import ForecastOut
from src.crud.may_bom import get_may_bom_by_id
from src.crud.du_lieu_du_bao import list_du_lieu_du_bao_for_user, create_du_lieu_du_bao
from src.crud.thong_bao import create_notification
from src.api.v1.endpoints.admin_alerts import send_alert_to_admins_for_user_device_error
from src.models.du_lieu_du_bao import DuLieuDuBao
from src.models.nhat_ky_may_bom import NhatKyMayBom
from src.models.du_lieu_cam_bien import DuLieuCamBien

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
        # Gửi alert tới admin
        await send_alert_to_admins_for_user_device_error(
            db=db,
            ma_may_bom=ma_may_bom,
            error_type="forecast_error",
            error_details="Mô hình dự báo AI gặp lỗi khi xử lý dữ liệu"
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


@router.post("/predict", status_code=200, response_model=ForecastOut)
async def predict_flow(
    ma_may_bom: int = Query(...),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """
    Chạy mô hình dự báo dòng chảy cho máy bơm dựa trên dữ liệu cảm biến tại thời điểm bật máy gần nhất.
    """
    # Check pump
    pump = await get_may_bom_by_id(db, ma_may_bom)
    if not pump:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập máy bơm này")

    # Load Model
    try:
        model_path = os.path.join(os.path.dirname(__file__), "../../../predict/mo_hinh_random_forest.joblib")
        model = joblib.load(model_path)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Model file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model: {str(e)}")

    # Get latest pump start time
    stmt = select(NhatKyMayBom).where(NhatKyMayBom.ma_may_bom == ma_may_bom).order_by(NhatKyMayBom.thoi_gian_bat.desc()).limit(1)
    log_res = await db.execute(stmt)
    latest_log = log_res.scalars().first()

    if not latest_log:
        reference_time = datetime.now()
    else:
        reference_time = latest_log.thoi_gian_bat

    # Ensure reference_time is naive if it's aware, to match DB column type
    if reference_time.tzinfo is not None:
        reference_time = reference_time.replace(tzinfo=None)

    # Get sensor data
    sensor_stmt = select(DuLieuCamBien).where(
        DuLieuCamBien.ma_may_bom == ma_may_bom,
        DuLieuCamBien.thoi_gian_tao <= reference_time
    ).order_by(DuLieuCamBien.thoi_gian_tao.desc()).limit(1)
    
    sensor_res = await db.execute(sensor_stmt)
    sensor_data = sensor_res.scalars().first()

    if not sensor_data:
        sensor_stmt = select(DuLieuCamBien).where(
            DuLieuCamBien.ma_may_bom == ma_may_bom
        ).order_by(DuLieuCamBien.thoi_gian_tao.desc()).limit(1)
        sensor_res = await db.execute(sensor_stmt)
        sensor_data = sensor_res.scalars().first()

    if not sensor_data:
        raise HTTPException(status_code=400, detail="Không tìm thấy dữ liệu cảm biến cho máy bơm này để dự báo")

    # Prepare Data
    input_data = pd.DataFrame({
        'mua': [sensor_data.mua if sensor_data.mua is not None else 0],
        'do_am_dat': [sensor_data.do_am_dat if sensor_data.do_am_dat is not None else 0],
        'nhiet_do': [sensor_data.nhiet_do if sensor_data.nhiet_do is not None else 0],
        'do_am': [sensor_data.do_am if sensor_data.do_am is not None else 0]
    })

    # Predict
    try:
        prediction = model.predict(input_data)
        predicted_flow = float(prediction[0])
        
        # Calculate confidence
        if hasattr(model, "estimators_"):
            # RandomForestRegressor
            preds = [tree.predict(input_data)[0] for tree in model.estimators_]
            std_dev = np.std(preds)
            mean_val = np.mean(preds)
            
            # Avoid division by zero
            if mean_val == 0:
                confidence = 1.0 if std_dev == 0 else 0.0
            else:
                # Coefficient of variation
                cv = std_dev / abs(mean_val)
                # Simple linear mapping: 0 CV -> 100% conf, 1 CV -> 0% conf
                confidence = max(0.0, 1.0 - cv)
        else:
            # Fallback if not RF or no estimators
            confidence = 0.9
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi chạy mô hình dự báo: {str(e)}")

    # Save to DB
    new_forecast = DuLieuDuBao(
        mo_hinh="RandomForest",
        thoi_diem_du_bao=datetime.now(),
        luu_luong_du_bao=predicted_flow,
        do_tin_cay=confidence,
        ma_nguoi_dung=current_user.ma_nguoi_dung,
        ma_may_bom=ma_may_bom,
        ma_mo_hinh=11
    )

    try:
        created_forecast = await create_du_lieu_du_bao(db, new_forecast)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu kết quả dự báo: {str(e)}")

    return ForecastOut.from_orm(created_forecast)
