import datetime
import re
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pathlib import Path
import shutil
from src.api import deps

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.put("/{ma_nhan_vien}/anh-dai-dien", status_code=200)
async def update_avatar_nhan_vien(
    ma_nhan_vien: int,
    file: UploadFile = File(),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """
    Cập nhật ảnh đại diện cho nhân viên theo mã nhân viên.
    """

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400, detail="Chỉ cho phép file ảnh (JPEG, PNG, WEBP)"
        )

    result = await db.execute(
        text(
            "SELECT ma_nhan_vien, anh_dai_dien FROM nhan_vien WHERE ma_nhan_vien = :ma_nhan_vien"
        ),
        {"ma_nhan_vien": ma_nhan_vien},
    )

    nhan_vien = result.fetchone()
    if not nhan_vien:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu nhân viên")

    if nhan_vien.anh_dai_dien:
        old_path = UPLOAD_DIR / nhan_vien.anh_dai_dien
        if old_path.exists():
            old_path.unlink()

    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = Path(file.filename).suffix
    file_name = f"{now}_{ma_nhan_vien}{ext}"
    file_path = UPLOAD_DIR / file_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    await db.execute(
        text(
            """
            UPDATE nhan_vien
            SET anh_dai_dien = :anh_dai_dien
            WHERE ma_nhan_vien = :ma_nhan_vien
        """
        ),
        {"anh_dai_dien": file_name, "ma_nhan_vien": ma_nhan_vien},
    )

    await db.commit()
    return {
        "message": "Cập nhật ảnh đại diện thành công!",
        "ma_nhan_vien": ma_nhan_vien,
        "anh_dai_dien": file_name,
    }