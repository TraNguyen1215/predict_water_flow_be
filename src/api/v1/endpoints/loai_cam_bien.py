import datetime
import re
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pathlib import Path
import shutil
from src.api import deps

router = APIRouter()

# Lấy thông tin loại cảm biến
@router.get("/", status_code=200)
async def get_loai_cam_bien(
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Lấy danh sách loại cảm biến.
    """

    result = await db.execute(
        text(
            "SELECT * FROM loai_cam_bien ORDER BY ma_loai_cam_bien"
        )
    )

    loai_cam_bien_list = result.fetchall()
    return {"data": [dict(row) for row in loai_cam_bien_list]}


# Lấy thông tin loại cảm biến theo mã
@router.get("/{ma_loai_cam_bien}", status_code=200)
async def get_loai_cam_bien_theo_ma(
    ma_loai_cam_bien: int,
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Lấy thông tin loại cảm biến theo mã loại cảm biến.
    """
    
    result = await db.execute(
        text(
            "SELECT * FROM loai_cam_bien WHERE ma_loai_cam_bien = :ma_loai_cam_bien"
        ),
        {"ma_loai_cam_bien": ma_loai_cam_bien},
    )
    
    loai_cam_bien = result.fetchone()
    if not loai_cam_bien:
        raise HTTPException(status_code=404, detail="Không tìm thấy loại cảm biến")
    
    return {"data": dict(loai_cam_bien)}

# Thêm loại cảm biến mới
@router.post("/", status_code=201)
async def create_loai_cam_bien(
    ten_loai_cam_bien: str = Body(...),
    mo_ta: str | None = Body(None),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Thêm loại cảm biến mới.
    """

    await db.execute(
        text(
            "INSERT INTO loai_cam_bien(ten_loai_cam_bien, mo_ta) VALUES(:ten_loai_cam_bien, :mo_ta)"
        ),
        {
            "ten_loai_cam_bien": ten_loai_cam_bien,
            "mo_ta": mo_ta,
        },
    )

    await db.commit()

    return {"message": "Thêm loại cảm biến thành công", "ten_loai_cam_bien": ten_loai_cam_bien}

# Cập nhật loại cảm biến
@router.put("/{ma_loai_cam_bien}", status_code=200)
async def update_loai_cam_bien(
    ma_loai_cam_bien: int,
    ten_loai_cam_bien: str = Body(...),
    mo_ta: str | None = Body(None),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Cập nhật loại cảm biến theo mã loại cảm biến.
    """

    result = await db.execute(
        text(
            "SELECT ma_loai_cam_bien FROM loai_cam_bien WHERE ma_loai_cam_bien = :ma_loai_cam_bien"
        ),
        {"ma_loai_cam_bien": ma_loai_cam_bien},
    )

    loai_cam_bien = result.fetchone()
    if not loai_cam_bien:
        raise HTTPException(status_code=404, detail="Không tìm thấy loại cảm biến")

    await db.execute(
        text(
            """
            UPDATE loai_cam_bien
            SET ten_loai_cam_bien = :ten_loai_cam_bien,
                mo_ta = :mo_ta
            WHERE ma_loai_cam_bien = :ma_loai_cam_bien
        """
        ),
        {
            "ten_loai_cam_bien": ten_loai_cam_bien,
            "mo_ta": mo_ta,
            "ma_loai_cam_bien": ma_loai_cam_bien,
        },
    )

    await db.commit()
    return {
        "message": "Cập nhật loại cảm biến thành công!",
        "ma_loai_cam_bien": ma_loai_cam_bien,
    }

# Xoá loại cảm biến
@router.delete("/{ma_loai_cam_bien}", status_code=200)
async def delete_loai_cam_bien(
    ma_loai_cam_bien: int,
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Xoá loại cảm biến theo mã loại cảm biến.
    """

    result = await db.execute(
        text(
            "SELECT ma_loai_cam_bien FROM loai_cam_bien WHERE ma_loai_cam_bien = :ma_loai_cam_bien"
        ),
        {"ma_loai_cam_bien": ma_loai_cam_bien},
    )

    loai_cam_bien = result.fetchone()
    if not loai_cam_bien:
        raise HTTPException(status_code=404, detail="Không tìm thấy loại cảm biến")

    await db.execute(
        text(
            "DELETE FROM loai_cam_bien WHERE ma_loai_cam_bien = :ma_loai_cam_bien"
        ),
        {"ma_loai_cam_bien": ma_loai_cam_bien},
    )

    await db.commit()
    return {
        "message": "Xoá loại cảm biến thành công!",
        "ma_loai_cam_bien": ma_loai_cam_bien,
    }