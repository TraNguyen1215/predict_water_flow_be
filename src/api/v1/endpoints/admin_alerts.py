"""
Xử lý các ALERT dành cho ADMIN
Admin nhận toàn bộ ALERT liên quan đến hệ thống
"""

from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from src.api import deps
from src.crud.thong_bao import create_notification
from src.crud.nguoi_dung import get_all_admins
from src.crud.may_bom import get_may_bom_by_id
from src.models.du_lieu_cam_bien import DuLieuCamBien
from datetime import datetime, timedelta

router = APIRouter()


async def _send_alert_to_admins(
    db: AsyncSession,
    tieu_de: str,
    noi_dung: str,
    muc_do: str = "HIGH",
    du_lieu_lien_quan: Optional[dict] = None
):
    """Gửi ALERT tới tất cả admin"""
    admins = await get_all_admins(db)
    for admin in admins:
        await create_notification(
            db=db,
            ma_nguoi_dung=admin.ma_nguoi_dung,
            loai="ALERT",
            muc_do=muc_do,
            tieu_de=tieu_de,
            noi_dung=noi_dung,
            du_lieu_lien_quan=du_lieu_lien_quan or {}
        )


async def check_forecast_model_error_system_wide(db: AsyncSession, ma_may_bom: Optional[int] = None):
    """
    ALERT: Lỗi mô hình dự báo ảnh hưởng toàn hệ thống
    Kiểm tra nếu model dự báo có lỗi toàn hệ thống
    """
    # Lấy số lỗi dự báo trong 1 giờ gần đây
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    q = text("""
        SELECT COUNT(*) as error_count FROM du_lieu_du_bao
        WHERE mo_hoa_duy_bao_error = true AND thoi_gian_tao >= :one_hour_ago
    """)
    
    result = await db.execute(q, {"one_hour_ago": one_hour_ago})
    error_count = result.scalar() or 0
    
    # Nếu có nhiều lỗi, gửi alert tới admin
    if error_count > 5:
        await _send_alert_to_admins(
            db=db,
            tieu_de="⚠️ Lỗi mô hình dự báo ảnh hưởng hệ thống",
            noi_dung=f"Mô hình dự báo AI gặp lỗi {error_count} lần trong 1 giờ gần đây. Dự báo có thể không chính xác trên toàn hệ thống. Cần kiểm tra và xử lý ngay lập tức.",
            muc_do="HIGH",
            du_lieu_lien_quan={"error_count": error_count}
        )


async def check_database_error(db: AsyncSession, error_message: str):
    """
    ALERT: Lỗi database
    Lỗi cơ sở dữ liệu cần admin xử lý ngay
    """
    await _send_alert_to_admins(
        db=db,
        tieu_de="🔴 Lỗi cơ sở dữ liệu",
        noi_dung=f"Phát hiện lỗi cơ sở dữ liệu: {error_message}\n\nAdmin cần kiểm tra và xử lý ngay lập tức để tránh mất dữ liệu.",
        muc_do="HIGH",
        du_lieu_lien_quan={"error_type": "database_error", "error_message": error_message}
    )


async def check_mqtt_broker_disconnected(db: AsyncSession):
    """
    ALERT: MQTT broker mất kết nối
    Hệ thống IoT không thể nhận dữ liệu từ thiết bị
    """
    await _send_alert_to_admins(
        db=db,
        tieu_de="🌐 MQTT Broker mất kết nối",
        noi_dung="MQTT broker đã mất kết nối. Hệ thống không thể nhận dữ liệu từ các thiết bị IoT. Admin cần kiểm tra broker và khôi phục kết nối ngay.",
        muc_do="HIGH",
        du_lieu_lien_quan={"issue": "mqtt_broker_disconnected"}
    )


async def check_multiple_sensors_offline(db: AsyncSession):
    """
    ALERT: 5+ cảm biến offline đồng thời
    Kiểm tra nếu có nhiều cảm biến không hoạt động
    """
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    
    q = text("""
        SELECT mb.ma_may_bom, mb.ten_may_bom, COUNT(DISTINCT cc.ma_cam_bien) as offline_count
        FROM may_bom mb
        LEFT JOIN cam_bien cc ON mb.ma_may_bom = cc.ma_may_bom
        LEFT JOIN (
            SELECT DISTINCT ma_cam_bien FROM du_lieu_cam_bien
            WHERE thoi_gian_tao >= :five_minutes_ago
        ) du_lieu ON cc.ma_cam_bien = du_lieu.ma_cam_bien
        WHERE du_lieu.ma_cam_bien IS NULL AND cc.ma_cam_bien IS NOT NULL
        GROUP BY mb.ma_may_bom, mb.ten_may_bom
        HAVING COUNT(DISTINCT cc.ma_cam_bien) >= 5
    """)
    
    result = await db.execute(q, {"five_minutes_ago": five_minutes_ago})
    offline_sensors = result.fetchall()
    
    if offline_sensors:
        sensor_info = "\n".join([
            f"- Thiết bị '{row[1]}': {row[2]} cảm biến offline"
            for row in offline_sensors
        ])
        
        await _send_alert_to_admins(
            db=db,
            tieu_de="⚠️ 5+ cảm biến offline đồng thời",
            noi_dung=f"Phát hiện {len(offline_sensors)} thiết bị có 5+ cảm biến không hoạt động:\n\n{sensor_info}\n\nVui lòng kiểm tra kết nối thiết bị và cảm biến.",
            muc_do="HIGH",
            du_lieu_lien_quan={"offline_count": len(offline_sensors), "details": [
                {"pump_id": row[0], "pump_name": row[1], "sensor_offline_count": row[2]}
                for row in offline_sensors
            ]}
        )


async def check_no_data_in_system(db: AsyncSession):
    """
    ALERT: Không có dữ liệu trong toàn hệ thống
    Kiểm tra nếu không có dữ liệu cảm biến mới trong 10 phút
    """
    ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
    
    q = text("""
        SELECT COUNT(*) FROM du_lieu_cam_bien
        WHERE thoi_gian_tao >= :ten_minutes_ago
    """)
    
    result = await db.execute(q, {"ten_minutes_ago": ten_minutes_ago})
    recent_data_count = result.scalar() or 0
    
    if recent_data_count == 0:
        await _send_alert_to_admins(
            db=db,
            tieu_de="🔴 Không có dữ liệu trong toàn hệ thống",
            noi_dung="Hệ thống không nhận được bất kỳ dữ liệu cảm biến nào trong 10 phút qua. Đây là lỗi nghiêm trọng. Có thể:\n- MQTT broker mất kết nối\n- Tất cả thiết bị IoT offline\n- Lỗi hệ thống tập trung\n\nAdmin cần kiểm tra ngay lập tức.",
            muc_do="HIGH",
            du_lieu_lien_quan={"issue": "no_data_system_wide"}
        )


async def send_alert_to_admins_for_user_device_error(
    db: AsyncSession,
    ma_may_bom: int,
    error_type: str,
    error_details: str
):
    """
    ALERT: Lỗi thiết bị của bất kỳ user nào
    Admin giám sát toàn bộ lỗi thiết bị trong hệ thống
    """
    pump = await get_may_bom_by_id(db, ma_may_bom)
    pump_name = pump.ten_may_bom if pump else f"Thiết bị {ma_may_bom}"
    
    error_title_map = {
        "sensor_timeout": "Cảm biến mất dữ liệu",
        "abnormal_flow": "Lưu lượng nước bất thường",
        "humidity_trend": "Xu hướng độ ẩm bất thường",
        "flow_trend": "Xu hướng lưu lượng giảm",
        "watering_frequency": "Tần suất tưới bất thường",
        "forecast_error": "Lỗi dự báo"
    }
    
    title = error_title_map.get(error_type, "Lỗi thiết bị")
    
    await _send_alert_to_admins(
        db=db,
        tieu_de=f"⚠️ {title} - Thiết bị '{pump_name}'",
        noi_dung=f"Thiết bị: {pump_name}\n\nLỗi: {error_details}\n\nAdmin cần giám sát tình trạng thiết bị.",
        muc_do="MEDIUM",
        du_lieu_lien_quan={"error_type": error_type, "pump_name": pump_name}
    )


@router.get("/check-system-health", status_code=200)
async def check_system_health(
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """
    Manual endpoint để kiểm tra sức khỏe hệ thống
    Chỉ admin có quyền truy cập
    """
    if not getattr(current_user, "quan_tri_vien", False):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Chỉ admin có quyền truy cập")
    
    # Kiểm tra tất cả các điều kiện
    await check_forecast_model_error_system_wide(db)
    await check_multiple_sensors_offline(db)
    await check_no_data_in_system(db)
    
    return {
        "status": "ok",
        "message": "Hệ thống đã được kiểm tra. Nếu có lỗi, admin sẽ nhận được thông báo."
    }
