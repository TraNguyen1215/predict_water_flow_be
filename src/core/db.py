from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Please set DATABASE_URL environment variable"
    )

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,         # Số lượng kết nối tối đa trong pool
    max_overflow=20,      # Số kết nối vượt quá pool_size
    pool_timeout=30.0,    # Thời gian chờ để lấy kết nối từ pool
    pool_recycle=1800     # Tái sử dụng kết nối sau 30 phút
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise