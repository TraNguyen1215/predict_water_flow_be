import math
import datetime
import re
from pathlib import Path
import aiofiles
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.schemas.tep_ma_nhung import *
from src.crud.tep_ma_nhung import *

UPLOAD_DIR = Path("uploads/tep_ma_nhung")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 8 * 1024 * 1024))

router = APIRouter()


def _to_schema(obj) -> TepMaNhungOut:
    return TepMaNhungOut(
        ma_tep_ma_nhung=getattr(obj, "ma_tep_ma_nhung", None),
        ten_tep=getattr(obj, "ten_tep", None),
        phien_ban=getattr(obj, "phien_ban", None),
        mo_ta=getattr(obj, "mo_ta", None),
        url=getattr(obj, "url", None),
        thoi_gian_tao=getattr(obj, "thoi_gian_tao", None),
        thoi_gian_cap_nhat=getattr(obj, "thoi_gian_cap_nhat", None),
    )


@router.get("/", status_code=200)
async def list_tep_ma_nhung_endpoint(
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách tệp mã nhúng"""

    if page is not None:
        offset = (page - 1) * limit

    rows, total = await list_tep_ma_nhung(db, limit=limit, offset=offset)
    data = [_to_schema(r) for r in rows]
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    return {
        "data": data,
        "limit": limit,
        "offset": offset,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    }


@router.get("/{ma_tep_ma_nhung}", status_code=200, response_model=TepMaNhungOut)
async def get_tep_ma_nhung_endpoint(
    ma_tep_ma_nhung: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Chi tiết tệp mã nhúng."""

    obj = await get_tep_ma_nhung_by_id(db, ma_tep_ma_nhung)
    if not obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp mã nhúng")
    return _to_schema(obj)


@router.post("/", status_code=201, response_model=TepMaNhungOut)
async def create_tep_ma_nhung_endpoint(
    ten_tep: str = Form(...),
    phien_ban: Optional[str] = Form(None),
    mo_ta: Optional[str] = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Thêm tệp mã nhúng mới."""

    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới được phép thêm tệp mã nhúng")

    file_name = None
    if file is not None:
        contents = await file.read()
        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail=f"File quá lớn (tối đa {MAX_UPLOAD_SIZE} bytes)")

        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = Path(file.filename).suffix
        safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", ten_tep)
        file_name = f"{now}_{safe_name}{ext}"
        file_path = UPLOAD_DIR / file_name

        async with aiofiles.open(file_path, "wb") as out_file:
            await out_file.write(contents)

    payload = TepMaNhungCreate(ten_tep=ten_tep, phien_ban=phien_ban, mo_ta=mo_ta, url=file_name)
    obj = await create_tep_ma_nhung(db, payload)
    await db.commit()
    await db.refresh(obj)
    return _to_schema(obj)


@router.put("/{ma_tep_ma_nhung}", status_code=200, response_model=TepMaNhungOut)
async def update_tep_ma_nhung_endpoint(
    ma_tep_ma_nhung: int,
    ten_tep: Optional[str] = Form(None),
    phien_ban: Optional[str] = Form(None),
    mo_ta: Optional[str] = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật tệp mã nhúng."""

    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới được phép cập nhật tệp mã nhúng")

    existing = await get_tep_ma_nhung_by_id(db, ma_tep_ma_nhung)
    if not existing:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp mã nhúng")

    file_name = None
    if file is not None:
        contents = await file.read()
        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail=f"File quá lớn (tối đa {MAX_UPLOAD_SIZE} bytes)")

        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = Path(file.filename).suffix
        safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", ten_tep or existing.ten_tep or str(ma_tep_ma_nhung))
        file_name = f"{now}_{safe_name}{ext}"
        file_path = UPLOAD_DIR / file_name

        # remove old file if exists
        if existing.url:
            old_path = UPLOAD_DIR / existing.url
            if old_path.exists():
                try:
                    old_path.unlink()
                except Exception:
                    pass

        async with aiofiles.open(file_path, "wb") as out_file:
            await out_file.write(contents)

    payload = TepMaNhungUpdate(ten_tep=ten_tep, phien_ban=phien_ban, mo_ta=mo_ta, url=file_name)
    obj = await update_tep_ma_nhung(db, ma_tep_ma_nhung, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp mã nhúng")
    await db.commit()
    await db.refresh(obj)
    return _to_schema(obj)


@router.delete("/{ma_tep_ma_nhung}", status_code=200)
async def delete_tep_ma_nhung_endpoint(
    ma_tep_ma_nhung: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá tệp mã nhúng."""

    if not getattr(current_user, "quan_tri_vien", False):
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới được phép xoá tệp mã nhúng")

    deleted = await delete_tep_ma_nhung(db, ma_tep_ma_nhung)
    if not deleted:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp mã nhúng")
    await db.commit()
    return {
        "message": "Xoá tệp mã nhúng thành công",
        "ma_tep_ma_nhung": ma_tep_ma_nhung,
    }
