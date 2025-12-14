from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta
import logging
import asyncio
from .config import settings

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper function to run async coroutines in background scheduler"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Nếu loop đang chạy, tạo task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            # Nếu loop không chạy, chạy trực tiếp
            return asyncio.run(coro)
    except RuntimeError:
        # Nếu không có loop, tạo mới
        return asyncio.run(coro)


async def send_weekly_reports():
    """Gửi báo cáo hàng tuần - chạy 7h sáng Chủ nhật"""
    try:
        from src.crud.nguoi_dung import list_users
        from src.crud.may_bom import list_may_bom_for_user
        from src.crud import thong_bao as crud_thong_bao
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        
        # Tạo async session
        async_engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            # Lấy tất cả người dùng
            users, total, _, _, _, _ = await list_users(db, limit=10000, offset=0)
            
            sent_count = 0
            for user in users:
                # Lấy danh sách máy bơm của user
                pumps, _ = await list_may_bom_for_user(db, user.ma_nguoi_dung, limit=100, offset=0)
                
                if pumps:
                    from src.api.v1.endpoints.thong_bao import _generate_weekly_report
                    
                    report_content = "📊 **Báo cáo tuần**\n\n"
                    
                    for pump in pumps:
                        weekly_data = await _generate_weekly_report(db, user.ma_nguoi_dung, pump.ma_may_bom)
                        report_content += f"**Thiết bị: {pump.ten_may_bom}**\n"
                        report_content += f"- Số lần tưới: {weekly_data['watering_count']} lần\n"
                        report_content += f"- Độ ẩm trung bình: {weekly_data['avg_humidity']}%\n"
                        report_content += f"- Tổng lưu lượng: {weekly_data['total_flow']} lít\n"
                        report_content += f"- Kỳ: {weekly_data['period']}\n\n"
                    
                    # Gửi thông báo
                    await crud_thong_bao.create_notification(
                        db=db,
                        ma_nguoi_dung=user.ma_nguoi_dung,
                        loai="INFO",
                        muc_do="MEDIUM",
                        tieu_de="Báo cáo tuần của bạn",
                        noi_dung=report_content,
                        du_lieu_lien_quan={"type": "weekly_report"}
                    )
                    sent_count += 1
            
            await db.commit()
            logger.info(f"Gửi báo cáo hàng tuần thành công cho {sent_count} người dùng")
    except Exception as e:
        logger.error(f"Lỗi khi gửi báo cáo hàng tuần: {str(e)}")


async def send_monthly_reports():
    """Gửi báo cáo hàng tháng - chạy 7h sáng ngày cuối cùng của tháng"""
    try:
        from src.crud.nguoi_dung import list_users
        from src.crud.may_bom import list_may_bom_for_user
        from src.crud import thong_bao as crud_thong_bao
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        
        # Tạo async session
        async_engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            # Lấy tất cả người dùng
            users, total, _, _, _, _ = await list_users(db, limit=10000, offset=0)
            
            sent_count = 0
            for user in users:
                # Lấy danh sách máy bơm của user
                pumps, _ = await list_may_bom_for_user(db, user.ma_nguoi_dung, limit=100, offset=0)
                
                if pumps:
                    from src.api.v1.endpoints.thong_bao import _generate_monthly_report
                    
                    report_content = "📊 **Báo cáo tháng**\n\n"
                    
                    for pump in pumps:
                        monthly_data = await _generate_monthly_report(db, user.ma_nguoi_dung, pump.ma_may_bom)
                        report_content += f"**Thiết bị: {pump.ten_may_bom}**\n"
                        report_content += f"- Số lần tưới: {monthly_data['watering_count']} lần\n"
                        report_content += f"- Độ ẩm trung bình: {monthly_data['avg_humidity']}%\n"
                        report_content += f"- Tổng lưu lượng: {monthly_data['total_flow']} lít\n"
                        report_content += f"- Kỳ: {monthly_data['period']}\n\n"
                    
                    # Gửi thông báo
                    await crud_thong_bao.create_notification(
                        db=db,
                        ma_nguoi_dung=user.ma_nguoi_dung,
                        loai="INFO",
                        muc_do="MEDIUM",
                        tieu_de="Báo cáo tháng của bạn",
                        noi_dung=report_content,
                        du_lieu_lien_quan={"type": "monthly_report"}
                    )
                    sent_count += 1
            
            await db.commit()
            logger.info(f"Gửi báo cáo hàng tháng thành công cho {sent_count} người dùng")
    except Exception as e:
        logger.error(f"Lỗi khi gửi báo cáo hàng tháng: {str(e)}")


def start_scheduler():
    """Khởi động scheduler"""
    scheduler = BackgroundScheduler()
    
    # Job: Gửi báo cáo hàng tuần - 7h sáng Chủ nhật
    scheduler.add_job(
        lambda: run_async(send_weekly_reports()),
        CronTrigger(day_of_week=6, hour=7, minute=0),  # 6 = Chủ nhật, 7h, 0 phút
        id="weekly_report",
        name="Weekly Report",
        replace_existing=True
    )
    
    # Job: Gửi báo cáo hàng tháng - 7h sáng ngày cuối cùng của tháng
    # Sử dụng day_of_month=-1 để chỉ ngày cuối cùng của tháng
    scheduler.add_job(
        lambda: run_async(send_monthly_reports()),
        CronTrigger(day="last", hour=7, minute=0),
        id="monthly_report",
        name="Monthly Report",
        replace_existing=True
    )
    
    # Job: Gửi dashboard metrics hàng ngày - 8h sáng mỗi ngày
    scheduler.add_job(
        lambda: run_async(send_daily_dashboard_metrics()),
        CronTrigger(hour=8, minute=0),  # 8h mỗi sáng
        id="daily_dashboard_metrics",
        name="Daily Dashboard Metrics",
        replace_existing=True
    )
    
    # Job: Kiểm tra sức khỏe hệ thống - mỗi 30 phút
    scheduler.add_job(
        lambda: run_async(check_system_health_periodic()),
        CronTrigger(minute="0,30"),  # Mỗi 30 phút
        id="system_health_check",
        name="System Health Check",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler khởi động thành công")
    
    return scheduler


async def send_daily_dashboard_metrics():
    """Gửi metrics hàng ngày (lưu lượng, độ ẩm) cho users - chạy 8h sáng mỗi ngày"""
    try:
        from src.crud.nguoi_dung import list_users
        from src.crud.may_bom import list_may_bom_for_user
        from src.crud import thong_bao as crud_thong_bao
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import text
        
        # Tạo async session
        async_engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            # Lấy tất cả người dùng
            users, total, _, _, _, _ = await list_users(db, limit=10000, offset=0)
            
            sent_count = 0
            today = date.today()
            
            for user in users:
                # Lấy danh sách máy bơm của user
                pumps, _ = await list_may_bom_for_user(db, user.ma_nguoi_dung, limit=100, offset=0)
                
                if pumps:
                    dashboard_content = "📈 **Dữ liệu Dashboard Hôm Nay**\n\n"
                    
                    for pump in pumps:
                        # Lấy dữ liệu lưu lượng hôm nay
                        q_flow = text("""
                            SELECT DATE(thoi_gian_tao) as ngay, AVG(luu_luong) as avg_flow, MAX(luu_luong) as max_flow, MIN(luu_luong) as min_flow
                            FROM du_lieu_cam_bien
                            WHERE ma_may_bom = :ma_may_bom AND DATE(thoi_gian_tao) = :today AND luu_luong IS NOT NULL
                            GROUP BY DATE(thoi_gian_tao)
                        """)
                        
                        result_flow = await db.execute(q_flow, {"ma_may_bom": pump.ma_may_bom, "today": today})
                        flow_data = result_flow.fetchone()
                        
                        # Lấy dữ liệu độ ẩm hôm nay
                        q_humidity = text("""
                            SELECT DATE(thoi_gian_tao) as ngay, AVG(do_am) as avg_humidity, MAX(do_am) as max_humidity, MIN(do_am) as min_humidity
                            FROM du_lieu_cam_bien
                            WHERE ma_may_bom = :ma_may_bom AND DATE(thoi_gian_tao) = :today AND do_am IS NOT NULL
                            GROUP BY DATE(thoi_gian_tao)
                        """)
                        
                        result_humidity = await db.execute(q_humidity, {"ma_may_bom": pump.ma_may_bom, "today": today})
                        humidity_data = result_humidity.fetchone()
                        
                        dashboard_content += f"**{pump.ten_may_bom}:**\n"
                        
                        if flow_data:
                            avg_flow, max_flow, min_flow = flow_data[1], flow_data[2], flow_data[3]
                            dashboard_content += f"  📊 Lưu lượng: Trung bình {avg_flow:.2f} (Min: {min_flow:.2f}, Max: {max_flow:.2f})\n"
                        else:
                            dashboard_content += f"  📊 Lưu lượng: Chưa có dữ liệu\n"
                        
                        if humidity_data:
                            avg_humidity, max_humidity, min_humidity = humidity_data[1], humidity_data[2], humidity_data[3]
                            dashboard_content += f"  💧 Độ ẩm: Trung bình {avg_humidity:.1f}% (Min: {min_humidity:.1f}%, Max: {max_humidity:.1f}%)\n"
                        else:
                            dashboard_content += f"  💧 Độ ẩm: Chưa có dữ liệu\n"
                        
                        dashboard_content += "\n"
                    
                    # Gửi thông báo
                    await crud_thong_bao.create_notification(
                        db=db,
                        ma_nguoi_dung=user.ma_nguoi_dung,
                        loai="INFO",
                        muc_do="LOW",
                        tieu_de="Dashboard Metrics - Hôm nay",
                        noi_dung=dashboard_content,
                        du_lieu_lien_quan={"type": "daily_dashboard", "date": today.isoformat()}
                    )
                    sent_count += 1
            
            await db.commit()
            logger.info(f"Gửi dashboard metrics hàng ngày thành công cho {sent_count} người dùng")
    except Exception as e:
        logger.error(f"Lỗi khi gửi dashboard metrics: {str(e)}")


async def check_system_health_periodic():
    """Kiểm tra sức khỏe hệ thống định kỳ (mỗi 30 phút)"""
    try:
        from src.api.v1.endpoints.admin_alerts import (
            check_forecast_model_error_system_wide,
            check_multiple_sensors_offline,
            check_no_data_in_system
        )
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        
        # Tạo async session
        async_engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            # Kiểm tra các điều kiện sức khỏe hệ thống
            await check_forecast_model_error_system_wide(db)
            await check_multiple_sensors_offline(db)
            await check_no_data_in_system(db)
            
            await db.commit()
            logger.info("Kiểm tra sức khỏe hệ thống hoàn tất")
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra sức khỏe hệ thống: {str(e)}")
