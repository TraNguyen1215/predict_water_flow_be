from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import AsyncSessionLocal
from src.core import security
from sqlalchemy import text
import uuid

security_scheme = HTTPBearer()


async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    """Validate bearer token and return the user row from DB."""
    token = credentials.credentials
    payload = security.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # Validate UUID format
    try:
        user_uuid = uuid.UUID(str(user_id))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    result = await db.execute(text("SELECT ma_nguoi_dung, ten_dang_nhap FROM nguoi_dung WHERE ma_nguoi_dung = :ma"), {"ma": str(user_uuid)})
    user = result.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user