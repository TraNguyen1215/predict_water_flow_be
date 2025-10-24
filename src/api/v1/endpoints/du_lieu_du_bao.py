from typing import Optional
import math
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import deps
from src.schemas.du_lieu_du_bao import ForecastOut
from src.crud.may_bom import get_may_bom_by_id
from src.crud.du_lieu_du_bao import list_du_lieu_du_bao_for_user

router = APIRouter()


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
