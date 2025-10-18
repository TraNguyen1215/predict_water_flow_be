from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Body, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api import deps

router = APIRouter()


@router.post("/nhat-ky-may-bom", status_code=201)
async def create_nhat_ky(
    ma_may_bom: int = Body(..., embed=True),
    thoi_gian_bat: Optional[date] = Body(None, embed=True),
    thoi_gian_tat: Optional[date] = Body(None, embed=True),
    ghi_chu: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Tạo nhật ký cho máy bơm (chỉ chủ sở hữu)."""
    
    r = await db.execute(text("SELECT ma_nguoi_dung FROM may_bom WHERE ma_may_bom = :ma"), {"ma": ma_may_bom})
    pump = r.fetchone()
    
    if not pump:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép tạo nhật ký cho máy bơm này")

    result = await db.execute(
        text(
            "INSERT INTO nhat_ky_may_bom(ma_may_bom, thoi_gian_bat, thoi_gian_tat, ghi_chu, thoi_gian_tao) VALUES(:ma, :bat, :tat, :ghi, NOW()) RETURNING ma_nhat_ky"
        ),
        {"ma": ma_may_bom, "bat": thoi_gian_bat, "tat": thoi_gian_tat, "ghi": ghi_chu},
    )
    
    inserted = result.fetchone()
    await db.commit()
    
    ma = inserted.ma_nhat_ky if inserted else None
    
    return {"ma_nhat_ky": ma, "ma_may_bom": ma_may_bom}


@router.get("/nhat-ky-may-bom", status_code=200)
async def list_nhat_ky(
    ma_may_bom: int = Query(...),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Danh sách nhật ký cho một máy bơm (chỉ chủ sở hữu)."""
    
    r = await db.execute(text("SELECT ma_nguoi_dung FROM may_bom WHERE ma_may_bom = :ma"), {"ma": ma_may_bom})
    pump = r.fetchone()
    
    if not pump:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy bơm")
    if str(pump.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập nhật ký của máy bơm này")

    result = await db.execute(
        text(
            "SELECT ma_nhat_ky, ma_may_bom, thoi_gian_bat, thoi_gian_tat, ghi_chu, thoi_gian_tao FROM nhat_ky_may_bom WHERE ma_may_bom = :ma ORDER BY thoi_gian_tao DESC LIMIT :lim OFFSET :off"
        ),
        {"ma": ma_may_bom, "lim": limit, "off": offset},
    )
    
    rows = result.fetchall()
    items = [
        {
            "ma_nhat_ky": r.ma_nhat_ky,
            "ma_may_bom": r.ma_may_bom,
            "thoi_gian_bat": r.thoi_gian_bat,
            "thoi_gian_tat": r.thoi_gian_tat,
            "ghi_chu": r.ghi_chu,
            "thoi_gian_tao": r.thoi_gian_tao,
        }
        for r in rows
    ]
    
    return {"data": items, "limit": limit, "offset": offset, "total": len(items)}


@router.get("/nhat-ky-may-bom/{ma_nhat_ky}", status_code=200)
async def get_nhat_ky(
    ma_nhat_ky: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Lấy thông tin nhật ký theo mã nhật ký (chỉ chủ sở hữu)."""
    
    result = await db.execute(
        text(
            "SELECT n.ma_nhat_ky, n.ma_may_bom, m.ten_may_bom, n.thoi_gian_bat, n.thoi_gian_tat, n.ghi_chu, n.thoi_gian_tao, m.ma_nguoi_dung FROM nhat_ky_may_bom n JOIN may_bom m ON n.ma_may_bom = m.ma_may_bom WHERE n.ma_nhat_ky = :ma"
        ),
        {"ma": ma_nhat_ky},
    )
    r = result.fetchone()
    
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép truy cập nhật ký của người khác")
    
    return {
        "ma_nhat_ky": r.ma_nhat_ky,
        "ma_may_bom": r.ma_may_bom,
        "ten_may_bom": r.ten_may_bom,
        "thoi_gian_bat": r.thoi_gian_bat,
        "thoi_gian_tat": r.thoi_gian_tat,
        "ghi_chu": r.ghi_chu,
        "thoi_gian_tao": r.thoi_gian_tao,
    }


@router.put("/nhat-ky-may-bom/{ma_nhat_ky}", status_code=200)
async def update_nhat_ky(
    ma_nhat_ky: int,
    thoi_gian_bat: Optional[date] = Body(None, embed=True),
    thoi_gian_tat: Optional[date] = Body(None, embed=True),
    ghi_chu: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Cập nhật nhật ký (chỉ chủ sở hữu)."""
    
    result = await db.execute(
        text(
            "SELECT n.ma_nhat_ky, n.ma_may_bom, m.ma_nguoi_dung FROM nhat_ky_may_bom n JOIN may_bom m ON n.ma_may_bom = m.ma_may_bom WHERE n.ma_nhat_ky = :ma"
        ),
        {"ma": ma_nhat_ky},
    )
    r = result.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép chỉnh sửa nhật ký của người khác")

    await db.execute(
        text(
            "UPDATE nhat_ky_may_bom SET thoi_gian_bat = :bat, thoi_gian_tat = :tat, ghi_chu = :ghi, thoi_gian_cap_nhat = NOW() WHERE ma_nhat_ky = :ma"
        ),
        {"bat": thoi_gian_bat, "tat": thoi_gian_tat, "ghi": ghi_chu, "ma": ma_nhat_ky},
    )
    await db.commit()
    
    return {"message": "Cập nhật nhật ký thành công", "ma_nhat_ky": ma_nhat_ky}


@router.delete("/nhat-ky-may-bom/{ma_nhat_ky}", status_code=200)
async def delete_nhat_ky(
    ma_nhat_ky: int,
    db: AsyncSession = Depends(deps.get_db_session),
    current_user=Depends(deps.get_current_user),
):
    """Xoá nhật ký (chỉ chủ sở hữu)."""
    
    result = await db.execute(
        text(
            "SELECT n.ma_nhat_ky, m.ma_nguoi_dung FROM nhat_ky_may_bom n JOIN may_bom m ON n.ma_may_bom = m.ma_may_bom WHERE n.ma_nhat_ky = :ma"
        ),
        {"ma": ma_nhat_ky},
    )
    r = result.fetchone()
    
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký")
    if str(r.ma_nguoi_dung) != str(current_user.ma_nguoi_dung):
        raise HTTPException(status_code=403, detail="Không được phép xoá nhật ký của người khác")

    await db.execute(text("DELETE FROM nhat_ky_may_bom WHERE ma_nhat_ky = :ma"), {"ma": ma_nhat_ky})
    await db.commit()
    
    return {"message": "Xoá nhật ký thành công", "ma_nhat_ky": ma_nhat_ky}
