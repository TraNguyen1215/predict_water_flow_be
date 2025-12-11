from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func
from uuid import UUID
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
from src.models.thong_bao import ThongBao
from src.models.nguoi_dung import NguoiDung
from src.schemas.thong_bao import ThongBaoCreate, ThongBaoUpdate
from src.core.config import settings


def send_sms_via_email(phone_number: str, message: str) -> bool:
    """

    """
    try:
        if not settings.SEND_SMS or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            return False
        
        # Clean phone number (remove dashes, spaces, parentheses)
        clean_phone = ''.join(filter(str.isdigit, phone_number))
        
        # Construct SMS gateway email address
        sms_email = settings.SMS_GATEWAY_EMAIL.format(phone=clean_phone) if '{phone}' in settings.SMS_GATEWAY_EMAIL else settings.SMS_GATEWAY_EMAIL
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = settings.SENDER_EMAIL
        msg['To'] = sms_email
        msg['Subject'] = ''
        msg.attach(MIMEText(message, 'plain'))
        
        # Send via SMTP
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return False


async def send_sms_async(phone_number: str, message: str) -> bool:
    """Async wrapper for sending SMS"""
    return await asyncio.to_thread(send_sms_via_email, phone_number, message)


async def get_user_phone_number(db: AsyncSession, ma_nguoi_dung: UUID) -> Optional[str]:
    """
    Fetch phone number from user by user ID
    
    Args:
        db: Database session
        ma_nguoi_dung: User ID
    
    Returns:
        Phone number if user exists and has phone number, None otherwise
    """
    try:
        user_q = select(NguoiDung).where(NguoiDung.ma_nguoi_dung == ma_nguoi_dung)
        user_res = await db.execute(user_q)
        user = user_res.scalars().first()
        
        if not user:
            print(f"User with ID {ma_nguoi_dung} not found")
            return None
        
        if not user.so_dien_thoai:
            print(f"User {ma_nguoi_dung} does not have a phone number")
            return None
        
        return user.so_dien_thoai
    except Exception as e:
        print(f"Error fetching user phone number: {str(e)}")
        return None


async def create_notification(
    db: AsyncSession,
    ma_nguoi_dung: UUID,
    loai: str,
    muc_do: str,
    tieu_de: str,
    noi_dung: str,
    ma_thiet_bi: Optional[int] = None,
    du_lieu_lien_quan: Optional[Any] = None,
    gui_sms: bool = False,
) -> ThongBao:
    """Helper function to create notification from other operations"""
    # Fetch user phone number
    so_dien_thoai = await get_user_phone_number(db, ma_nguoi_dung)
    
    notification = ThongBao(
        ma_nguoi_dung=ma_nguoi_dung,
        ma_thiet_bi=ma_thiet_bi,
        loai=loai,
        muc_do=muc_do,
        tieu_de=tieu_de,
        noi_dung=noi_dung,
        du_lieu_lien_quan=du_lieu_lien_quan,
        so_dien_thoai=so_dien_thoai,
        gui_sms=gui_sms,
    )
    db.add(notification)
    await db.flush()
    
    # Send SMS if enabled and phone number provided
    if gui_sms and so_dien_thoai:
        message = f"{tieu_de}\n{noi_dung}"
        await send_sms_async(so_dien_thoai, message)
    
    return notification


async def create(db: AsyncSession, obj_in: ThongBaoCreate) -> ThongBao:
    # Fetch user phone number
    so_dien_thoai = await get_user_phone_number(db, obj_in.ma_nguoi_dung)
    
    db_obj = ThongBao(
        ma_nguoi_dung=obj_in.ma_nguoi_dung,
        ma_thiet_bi=obj_in.ma_thiet_bi,
        loai=obj_in.loai,
        muc_do=obj_in.muc_do,
        tieu_de=obj_in.tieu_de,
        noi_dung=obj_in.noi_dung,
        da_xem=obj_in.da_xem,
        so_dien_thoai=so_dien_thoai,
        gui_sms=obj_in.gui_sms,
        du_lieu_lien_quan=obj_in.du_lieu_lien_quan,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    # Send SMS if enabled and phone number provided
    if obj_in.gui_sms and so_dien_thoai:
        message = f"{obj_in.tieu_de}\n{obj_in.noi_dung}"
        await send_sms_async(so_dien_thoai, message)
    
    return db_obj


async def get_by_id(db: AsyncSession, ma_thong_bao: int) -> Optional[ThongBao]:
    q = select(ThongBao).where(ThongBao.ma_thong_bao == ma_thong_bao)
    res = await db.execute(q)
    return res.scalars().first()


async def get_by_user(
    db: AsyncSession, ma_nguoi_dung: UUID, skip: int = 0, limit: int = 100
) -> tuple[List[ThongBao], int]:
    # Get count
    count_q = select(func.count(ThongBao.ma_thong_bao)).where(
        ThongBao.ma_nguoi_dung == ma_nguoi_dung
    )
    count_res = await db.execute(count_q)
    total = count_res.scalar() or 0
    
    # Get data
    q = (
        select(ThongBao)
        .where(ThongBao.ma_nguoi_dung == ma_nguoi_dung)
        .order_by(desc(ThongBao.thoi_gian))
        .offset(skip)
        .limit(limit)
    )
    res = await db.execute(q)
    return res.scalars().all(), total


async def get_unread_by_user(
    db: AsyncSession, ma_nguoi_dung: UUID, skip: int = 0, limit: int = 100
) -> tuple[List[ThongBao], int]:
    # Get count
    count_q = select(func.count(ThongBao.ma_thong_bao)).where(
        (ThongBao.ma_nguoi_dung == ma_nguoi_dung) & (ThongBao.da_xem == False)
    )
    count_res = await db.execute(count_q)
    total = count_res.scalar() or 0
    
    # Get data
    q = (
        select(ThongBao)
        .where(
            (ThongBao.ma_nguoi_dung == ma_nguoi_dung) & (ThongBao.da_xem == False)
        )
        .order_by(desc(ThongBao.thoi_gian))
        .offset(skip)
        .limit(limit)
    )
    res = await db.execute(q)
    return res.scalars().all(), total


async def count_unread_by_user(db: AsyncSession, ma_nguoi_dung: UUID) -> int:
    q = select(
        func.count(ThongBao.ma_thong_bao)
    ).where((ThongBao.ma_nguoi_dung == ma_nguoi_dung) & (ThongBao.da_xem == False))
    res = await db.execute(q)
    return res.scalar() or 0


async def update(
    db: AsyncSession, ma_thong_bao: int, obj_in: ThongBaoUpdate
) -> Optional[ThongBao]:
    db_obj = await get_by_id(db, ma_thong_bao)
    if not db_obj:
        return None

    update_data = obj_in.dict(exclude_unset=True)
    q = (
        update(ThongBao)
        .where(ThongBao.ma_thong_bao == ma_thong_bao)
        .values(**update_data)
    )
    await db.execute(q)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def mark_as_read(db: AsyncSession, ma_thong_bao: int) -> Optional[ThongBao]:
    q = (
        update(ThongBao)
        .where(ThongBao.ma_thong_bao == ma_thong_bao)
        .values(da_xem=True)
    )
    await db.execute(q)
    await db.commit()
    return await get_by_id(db, ma_thong_bao)


async def mark_all_as_read(db: AsyncSession, ma_nguoi_dung: UUID) -> int:
    q = (
        update(ThongBao)
        .where((ThongBao.ma_nguoi_dung == ma_nguoi_dung) & (ThongBao.da_xem == False))
        .values(da_xem=True)
    )
    res = await db.execute(q)
    await db.commit()
    return res.rowcount


async def delete(db: AsyncSession, ma_thong_bao: int) -> bool:
    q = delete(ThongBao).where(ThongBao.ma_thong_bao == ma_thong_bao)
    res = await db.execute(q)
    await db.commit()
    return res.rowcount > 0


async def delete_by_user(db: AsyncSession, ma_nguoi_dung: UUID) -> int:
    q = delete(ThongBao).where(ThongBao.ma_nguoi_dung == ma_nguoi_dung)
    res = await db.execute(q)
    await db.commit()
    return res.rowcount
