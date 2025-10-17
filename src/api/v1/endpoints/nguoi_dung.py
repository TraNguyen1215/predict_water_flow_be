import datetime
import re
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api.auth import verify_token, UserInfo
from pathlib import Path
import shutil
from src.api import deps

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Lấy thông tin nhân viên
@router.get("/thong-tin-ca-nhan", status_code=200)
async def get_list(db: AsyncSession = Depends(deps.get_db_session), user: UserInfo = Depends(verify_token)):
    """
    Lấy thông tin nhân viên.
    """

    result = await db.execute(
        text("""
            SELECT * FROM nhan_vien WHERE ten_dang_nhap = :ten_dang_nhap;
        """),
        {"ten_dang_nhap": user.username}
    )

    nhan_vien = result.mappings().fetchone()
    if not nhan_vien:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu nhân viên")

    result_dv = await db.execute(
    text("""
        SELECT 
            dv.ma_don_vi,
            dv.ten, 
            dv.ten_viet_tat, 
            lk.chuc_vu
        FROM lien_ket_nhan_vien_don_vi lk
        JOIN don_vi dv ON lk.ma_don_vi = dv.ma_don_vi
        WHERE lk.ma_nhan_vien = :ma_nhan_vien
        ORDER BY lk.ngay_bat_dau DESC
        """),
        {"ma_nhan_vien": nhan_vien["ma_nhan_vien"]}
    )
    don_vi = result_dv.mappings().fetchone()

    return {
        'nhan_vien': nhan_vien,
        'don_vi': don_vi,
    }

# danh sách nhân viên
@router.get("/", status_code=200)
async def get_list(db: AsyncSession = Depends(deps.get_db_session), user: UserInfo = Depends(verify_token)):
    """
    Lấy danh sách nhân viên.
    """
    if "admin" in user.roles or "executive" in user.roles or "manage" in user.roles:
        query_nhan_vien = await db.execute(
            text("""
                SELECT
                    nv.*,
                    lknvd.ma_don_vi,
                    lknvd.chuc_vu,
                    dv.ten AS ten_don_vi,
                    dv.ten_viet_tat,
                    lklhdnv.ma_loai_hop_dong,
                    lhd.ten_loai_hop_dong,
                    lb.ten_lich_bieu,
                    lb.noi_dung
                FROM
                    nhan_vien nv
                LEFT JOIN lien_ket_nhan_vien_don_vi lknvd ON nv.ma_nhan_vien = lknvd.ma_nhan_vien
                LEFT JOIN don_vi dv ON lknvd.ma_don_vi = dv.ma_don_vi
                LEFT JOIN lien_ket_loai_hop_dong_nhan_vien lklhdnv ON nv.ma_nhan_vien = lklhdnv.ma_nhan_vien
                LEFT JOIN loai_hop_dong lhd ON lklhdnv.ma_loai_hop_dong = lhd.ma_loai_hop_dong
                LEFT JOIN lien_ket_lich_bieu_nhan_vien lknvlb ON nv.ma_nhan_vien = lknvlb.ma_nhan_vien
                LEFT JOIN lich_bieu lb ON lknvlb.ma_lich_bieu = lb.ma_lich_bieu
                ORDER BY nv.ma_nhan_vien ASC;
            """)
        )
        
        nhan_vien= [dict(row) for row in query_nhan_vien.mappings().all()]
        
        return {
            "tong_so_nhan_vien": len(nhan_vien),
            "du_lieu": nhan_vien
        }
    elif "employee" in user.roles:
        # lấy thông tin đơn vị của user
        query_user = await db.execute(
            text("""
                SELECT * FROM nhan_vien WHERE ten_dang_nhap = :ten_dang_nhap;
            """),
            {"ten_dang_nhap": user.username}
        )
        
        user = query_user.mappings().fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        
        # lấy thông tin đơn vị của user
        query_don_vi = await db.execute(
            text("""
                SELECT ma_don_vi FROM lien_ket_nhan_vien_don_vi WHERE ma_nhan_vien = :ma_nhan_vien;
            """),
            {"ma_nhan_vien": user["ma_nhan_vien"]}
        )  
        user_don_vi = query_don_vi.mappings().fetchone()

        if not user_don_vi:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị của người dùng")
        
        query_nhan_vien = await db.execute(
            text("""
                SELECT * FROM nhan_vien WHERE ma_nhan_vien IN (
                    SELECT ma_nhan_vien FROM lien_ket_nhan_vien_don_vi WHERE ma_don_vi = :ma_don_vi
                ) ORDER BY ma_nhan_vien ASC;
            """),
            {"ma_don_vi": user_don_vi["ma_don_vi"]}
        )

        nhan_vien = [dict(row) for row in query_nhan_vien.mappings().all()]

        return {
            "tong_so_nhan_vien": len(nhan_vien),
            "du_lieu": nhan_vien
        }
    else:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập vào dữ liệu này.")
    
# thêm mới nhân viên
@router.post("/", status_code=201)
async def create_nhan_vien(
    ho_ten: str = Body(...),
    ngay_sinh: datetime.date = Body(None),
    dia_chi: str = Body(None),
    email: str = Body(None),
    dien_thoai: str = Body(None),
    skype: str = Body(None),
    zalo: str = Body(None),
    facebook: str = Body(None),
    ma_may_cham_cong: int | None = Body(None),
    cham_cong: bool | None = Body(None),
    trang_thai: bool = Body(False),
    noi_bat: bool = Body(False),
    ten_dang_nhap: str = Body(None),
    ma_don_vi: int = Body(None),
    ma_loai_hop_dong: int = Body(None),
    chuc_vu: str = Body(None),
    ngay_bat_dau_hop_dong: datetime.date = Body(None),
    ngay_bat_dau_vao_lam: datetime.date = Body(None),
    ma_lich_bieu: int = Body(None),
    db: AsyncSession = Depends(deps.get_db_session),
    user: UserInfo = Depends(verify_token)
):
    if "admin" not in user.roles and "executive" not in user.roles:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập tạo dữ liệu.")

    # Kiểm tra bắt buộc
    if not all([ho_ten]):
        raise HTTPException(status_code=400, detail="Cần nhập đầy đủ thông tin")

    # email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    # if not re.match(email_regex, email):
    #     raise HTTPException(status_code=400, detail="Email không hợp lệ")
    # phone_regex = r"^\+?[0-9]{10,15}$"
    # if not re.match(phone_regex, dien_thoai):
    #     raise HTTPException(status_code=400, detail="Số điện thoại không hợp lệ")

    # Ép kiểu ma_loai_hop_dong nếu client gửi dạng chuỗi
    if isinstance(ma_loai_hop_dong, str) and ma_loai_hop_dong.isdigit():
        ma_loai_hop_dong = int(ma_loai_hop_dong)

    try:
        insert_stmt = text("""
            INSERT INTO nhan_vien (
                ho_ten, ngay_sinh, dia_chi, email, dien_thoai, skype, zalo, facebook,
                ma_may_cham_cong, cham_cong, trang_thai, noi_bat, ten_dang_nhap, ngay_vao_lam, ngay_ky_hdld, thoi_gian_tao
            ) VALUES (
                :ho_ten, :ngay_sinh, :dia_chi, :email, :dien_thoai, :skype, :zalo, :facebook,
                :ma_may_cham_cong, :cham_cong, :trang_thai, :noi_bat, :ten_dang_nhap, :ngay_vao_lam, :ngay_ky_hdld, NOW()
            ) RETURNING ma_nhan_vien
        """)
        res = await db.execute(insert_stmt, {
            "ho_ten": ho_ten.strip(),
            "ngay_sinh": ngay_sinh,
            "dia_chi": dia_chi.strip() if dia_chi else None,
            "email": email.strip() if email else None,
            "dien_thoai": dien_thoai.strip() if dien_thoai else None,
            "skype": skype,
            "zalo": zalo,
            "facebook": facebook,
            "ma_may_cham_cong": ma_may_cham_cong,
            "cham_cong": cham_cong,
            "trang_thai": trang_thai,
            "noi_bat": noi_bat,
            "ten_dang_nhap": ten_dang_nhap.lower().strip() if ten_dang_nhap else None,
            "ngay_vao_lam": ngay_bat_dau_vao_lam if ngay_bat_dau_vao_lam else None,
            "ngay_ky_hdld": ngay_bat_dau_hop_dong if ngay_bat_dau_hop_dong else None,
        })
        ma_nhan_vien_new = res.scalar()
        
        # Liên kết đơn vị
        if ma_don_vi and chuc_vu:
            await db.execute(text("""
                INSERT INTO lien_ket_nhan_vien_don_vi (ma_nhan_vien, ma_don_vi, chuc_vu, ngay_bat_dau, thoi_gian_tao)
                VALUES (:ma_nhan_vien, :ma_don_vi, :chuc_vu, :ngay_bat_dau, NOW())
            """), {
                "ma_nhan_vien": ma_nhan_vien_new,
                "ma_don_vi": ma_don_vi,
                "chuc_vu": chuc_vu,
                "ngay_bat_dau": ngay_bat_dau_vao_lam
            })

        # Liên kết hợp đồng
        if ma_loai_hop_dong:
            await db.execute(text("""
                INSERT INTO lien_ket_loai_hop_dong_nhan_vien (ma_nhan_vien, ma_loai_hop_dong, ngay_bat_dau, ngay_ket_thuc)
                VALUES (:ma_nhan_vien, :ma_loai_hop_dong, :ngay_bat_dau, :ngay_ket_thuc)
            """), {
                "ma_nhan_vien": ma_nhan_vien_new,
                "ma_loai_hop_dong": ma_loai_hop_dong,
                "ngay_bat_dau": None,
                "ngay_ket_thuc": None
            })

        # Liên kết lịch biểu
        if ma_lich_bieu:
            await db.execute(text("""
                INSERT INTO lien_ket_lich_bieu_nhan_vien (ma_nhan_vien, ma_lich_bieu, ngay_bat_dau)
                VALUES (:ma_nhan_vien, :ma_lich_bieu, :ngay_bat_dau)
            """), {
                "ma_nhan_vien": ma_nhan_vien_new,
                "ma_lich_bieu": ma_lich_bieu,
                "ngay_bat_dau": ngay_bat_dau_vao_lam
            })

        try:
            nam_init = (ngay_bat_dau_vao_lam.year if isinstance(ngay_bat_dau_vao_lam, datetime.date) else datetime.date.today().year)
            check_sdnp = await db.execute(
                text("""
                    SELECT 1 FROM so_du_nghi_phep
                    WHERE ma_nhan_vien = :ma_nhan_vien AND nam = :nam
                """),
                {"ma_nhan_vien": ma_nhan_vien_new, "nam": nam_init}
            )
            exists_sdnp = check_sdnp.scalar() is not None
            if not exists_sdnp:
                await db.execute(
                    text("""
                        INSERT INTO so_du_nghi_phep (ma_nhan_vien, nam, tong_ngay, da_dung, thoi_gian_tao)
                        VALUES (:ma_nhan_vien, :nam, :tong_ngay, :da_dung, :thoi_gian_tao)
                    """),
                    {
                        "ma_nhan_vien": ma_nhan_vien_new,
                        "nam": nam_init,
                        "tong_ngay": 12,
                        "da_dung": 0,
                        "thoi_gian_tao": datetime.datetime.utcnow(),
                    }
                )
        except Exception:
            pass

        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi tạo nhân viên: {str(e)}")

    return {"message": "Thêm mới nhân viên thành công!", "nhan_vien": {
        "ma_nhan_vien": ma_nhan_vien_new,
        "ho_ten": ho_ten,
        "dia_chi": dia_chi,
        "email": email,
        "dien_thoai": dien_thoai,
        "skype": skype,
        "zalo": zalo,
        "facebook": facebook,
        "ma_may_cham_cong": ma_may_cham_cong,
        "cham_cong": cham_cong,
        "trang_thai": trang_thai,
        "noi_bat": noi_bat,
        "ten_dang_nhap": ten_dang_nhap,
        "ma_don_vi": ma_don_vi,
        "ma_loai_hop_dong": ma_loai_hop_dong,
        "chuc_vu": chuc_vu,
        "ngay_ky_hdld": ngay_bat_dau_hop_dong,
        "ngay_bat_dau_vao_lam": ngay_bat_dau_vao_lam,
        "ma_lich_bieu": ma_lich_bieu
    }}

# chỉnh sửa thông tin nhân viên
@router.put("/{ma_nhan_vien}", status_code=200)
async def update_nhan_vien(
    ma_nhan_vien: int,
    ho_ten: str = Body(None),
    ngay_sinh: datetime.date = Body(None),
    dia_chi: str = Body(None),
    email: str = Body(None),
    dien_thoai: str = Body(None),
    skype: str = Body(None),
    zalo: str = Body(None),
    facebook: str = Body(None),
    ma_may_cham_cong: int | None = Body(None),
    trang_thai: bool = Body(None),
    noi_bat: bool = Body(None),
    cham_cong: bool = Body(None),
    ten_dang_nhap: str = Body(None),
    ma_don_vi: int = Body(None),
    ma_loai_hop_dong: int = Body(None),
    chuc_vu: str = Body(None),
    ngay_vao_lam: datetime.date = Body(None),
    ngay_ky_hdld: datetime.date = Body(None),
    ngay_bat_dau_hop_dong: datetime.date = Body(None),
    ngay_ket_thuc_hop_dong: datetime.date = Body(None),
    ma_lich_bieu: int = Body(None),
    db: AsyncSession = Depends(deps.get_db_session),
    user: UserInfo = Depends(verify_token)
):
    """
    Cập nhật thông tin nhân viên theo mã nhân viên.
    """
    # Kiểm tra sự tồn tại của nhân viên
    result = await db.execute(
        text("""
                SELECT 
                    nv.*,
                    lknvd.ma_don_vi,
                    lknvd.chuc_vu,
                    dv.ten AS ten_don_vi,
                    dv.ten_viet_tat,
                    lklhdnv.ma_loai_hop_dong,
                    lhd.ten_loai_hop_dong,
                    lklhdnv.ngay_bat_dau AS ngay_bat_dau_hop_dong,
                    lklhdnv.ngay_ket_thuc AS ngay_ket_thuc_hop_dong,
                    lb.ten_lich_bieu,
                    lb.ma_lich_bieu,
                    lb.noi_dung
                FROM
                    nhan_vien nv
                LEFT JOIN lien_ket_nhan_vien_don_vi lknvd ON nv.ma_nhan_vien = lknvd.ma_nhan_vien
                LEFT JOIN don_vi dv ON lknvd.ma_don_vi = dv.ma_don_vi
                LEFT JOIN lien_ket_loai_hop_dong_nhan_vien lklhdnv ON nv.ma_nhan_vien = lklhdnv.ma_nhan_vien
                LEFT JOIN loai_hop_dong lhd ON lklhdnv.ma_loai_hop_dong = lhd.ma_loai_hop_dong
                LEFT JOIN lien_ket_lich_bieu_nhan_vien lknvlb ON nv.ma_nhan_vien = lknvlb.ma_nhan_vien
                LEFT JOIN lich_bieu lb ON lknvlb.ma_lich_bieu = lb.ma_lich_bieu
                WHERE nv.ma_nhan_vien = :ma_nhan_vien
                ORDER BY nv.ma_nhan_vien ASC;"""),
        {"ma_nhan_vien": ma_nhan_vien}
    )
    nhan_vien = result.fetchone()

    if not nhan_vien:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu nhân viên")

    # Kiểm tra quyền: admin có thể update bất kỳ ai, các role khác chỉ update chính họ
    if "admin" not in user.roles:
        if nhan_vien.ten_dang_nhap != user.username:
            raise HTTPException(status_code=403, detail="Bạn chỉ có thể cập nhật thông tin của bản thân")

    update_data = {
        "ho_ten": ho_ten if ho_ten is not None else nhan_vien.ho_ten,
        "ngay_sinh": ngay_sinh if ngay_sinh is not None else nhan_vien.ngay_sinh,
        "dia_chi": dia_chi if dia_chi is not None else nhan_vien.dia_chi,
        "email": email if email is not None else nhan_vien.email,
        "dien_thoai": dien_thoai if dien_thoai is not None else nhan_vien.dien_thoai,
        "skype": skype if skype is not None else nhan_vien.skype,
        "zalo": zalo if zalo is not None else nhan_vien.zalo,
        "facebook": facebook if facebook is not None else nhan_vien.facebook,
        "ma_may_cham_cong": ma_may_cham_cong if ma_may_cham_cong is not None else nhan_vien.ma_may_cham_cong,
        "cham_cong": cham_cong if cham_cong is not None else nhan_vien.cham_cong,
        "trang_thai": trang_thai if trang_thai is not None else nhan_vien.trang_thai,
        "noi_bat": noi_bat if noi_bat is not None else nhan_vien.noi_bat,
        "ten_dang_nhap": ten_dang_nhap if ten_dang_nhap is not None else nhan_vien.ten_dang_nhap,
        "thoi_gian_cap_nhat": datetime.datetime.utcnow(),
        "ma_nhan_vien": ma_nhan_vien,
        "ngay_vao_lam": ngay_vao_lam if ngay_vao_lam is not None else nhan_vien.ngay_vao_lam,
        "ngay_ky_hdld": ngay_ky_hdld if ngay_ky_hdld is not None else nhan_vien.ngay_ky_hdld,
    }

    if email is not None:
        emailRegex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(emailRegex, email):
            raise HTTPException(status_code=400, detail="Email không hợp lệ")

    if dien_thoai is not None:
        phoneRegex = r"^\+?[0-9]{10,15}$"
        if not re.match(phoneRegex, dien_thoai):
            raise HTTPException(status_code=400, detail="Số điện thoại không hợp lệ")

    # Cập nhật dữ liệu
    await db.execute(
        text("""
            UPDATE nhan_vien
            SET ho_ten = :ho_ten,
                ngay_sinh = :ngay_sinh,
                dia_chi = :dia_chi,
                email = :email,
                dien_thoai = :dien_thoai,
                skype = :skype,
                zalo = :zalo,
                facebook = :facebook,
                ma_may_cham_cong = :ma_may_cham_cong,
                trang_thai = :trang_thai,
                noi_bat = :noi_bat,
                cham_cong = :cham_cong,
                ten_dang_nhap = :ten_dang_nhap,
                ngay_vao_lam = :ngay_vao_lam,
                ngay_ky_hdld = :ngay_ky_hdld,
                thoi_gian_cap_nhat = :thoi_gian_cap_nhat
            WHERE ma_nhan_vien = :ma_nhan_vien
        """),
        update_data
    )
    
    # Cập nhật thông tin liên kết đơn vị
    if ma_don_vi or chuc_vu:
        result = await db.execute(
            text("""
                UPDATE lien_ket_nhan_vien_don_vi
                SET ma_don_vi = :ma_don_vi,
                    chuc_vu = :chuc_vu
                WHERE ma_nhan_vien = :ma_nhan_vien
            """),
            {
                "ma_don_vi": ma_don_vi if ma_don_vi is not None else nhan_vien.ma_don_vi,
                "chuc_vu": chuc_vu if chuc_vu is not None else nhan_vien.chuc_vu,
                "ma_nhan_vien": ma_nhan_vien,
            }
        )
        if result.rowcount == 0:
            await db.execute(
                text("""
                    INSERT INTO lien_ket_nhan_vien_don_vi (ma_nhan_vien, ma_don_vi, chuc_vu)
                    VALUES (:ma_nhan_vien, :ma_don_vi, :chuc_vu)
                """),
                {
                    "ma_nhan_vien": ma_nhan_vien,
                    "ma_don_vi": ma_don_vi if ma_don_vi is not None else nhan_vien.ma_don_vi,
                    "chuc_vu": chuc_vu if chuc_vu is not None else nhan_vien.chuc_vu,
                }
            )
        # cập nhật bằng cách tạo mới và lấy bản ghi mới nhất
        # await db.execute(
        #         text("""
        #             INSERT INTO lien_ket_nhan_vien_don_vi (ma_nhan_vien, ma_don_vi, chuc_vu)
        #             VALUES (:ma_nhan_vien, :ma_don_vi, :chuc_vu)
        #         """),
        #         {
        #             "ma_nhan_vien": ma_nhan_vien,
        #             "ma_don_vi": ma_don_vi if ma_don_vi is not None else nhan_vien.ma_don_vi,
        #             "chuc_vu": chuc_vu if chuc_vu is not None else nhan_vien.chuc_vu,
        #         }
        #     )
        
        await db.commit()

    # Cập nhật thông tin liên kết loại hợp đồng
    if ma_loai_hop_dong or ngay_bat_dau_hop_dong or ngay_ket_thuc_hop_dong:
        result = await db.execute(
            text("""
                UPDATE lien_ket_loai_hop_dong_nhan_vien
                SET ma_loai_hop_dong = :ma_loai_hop_dong,
                    ngay_bat_dau = :ngay_bat_dau_hop_dong,
                    ngay_ket_thuc = :ngay_ket_thuc_hop_dong
                WHERE ma_nhan_vien = :ma_nhan_vien
            """),
            {
                "ma_loai_hop_dong": ma_loai_hop_dong if ma_loai_hop_dong is not None else nhan_vien.ma_loai_hop_dong,
                "ngay_bat_dau_hop_dong": ngay_bat_dau_hop_dong,
                "ngay_ket_thuc_hop_dong": ngay_ket_thuc_hop_dong if ngay_ket_thuc_hop_dong is not None else nhan_vien.ngay_ket_thuc_hop_dong,
                "ma_nhan_vien": ma_nhan_vien
            }
        )
        if result.rowcount == 0:
            await db.execute(
                text("""
                    INSERT INTO lien_ket_loai_hop_dong_nhan_vien (ma_nhan_vien, ma_loai_hop_dong, ngay_bat_dau, ngay_ket_thuc)
                    VALUES (:ma_nhan_vien, :ma_loai_hop_dong, :ngay_bat_dau_hop_dong, :ngay_ket_thuc_hop_dong)
                """),
                {
                    "ma_nhan_vien": ma_nhan_vien,
                    "ma_loai_hop_dong": ma_loai_hop_dong if ma_loai_hop_dong is not None else nhan_vien.ma_loai_hop_dong,
                    "ngay_bat_dau_hop_dong": ngay_bat_dau_hop_dong,
                    "ngay_ket_thuc_hop_dong": ngay_ket_thuc_hop_dong if ngay_ket_thuc_hop_dong is not None else nhan_vien.ngay_ket_thuc_hop_dong,
                }
            )
        await db.commit()
    
    # Cập nhật thông tin liên kết lịch biểu
    if ma_lich_bieu:
        result = await db.execute(
            text("""
                UPDATE lien_ket_lich_bieu_nhan_vien
                SET ma_lich_bieu = :ma_lich_bieu
                WHERE ma_nhan_vien = :ma_nhan_vien
            """),
            {
                "ma_lich_bieu": ma_lich_bieu if ma_lich_bieu is not None else nhan_vien.ma_lich_bieu,
                "ma_nhan_vien": ma_nhan_vien
            }
        )
        if result.rowcount == 0:
            await db.execute(
                text("""
                    INSERT INTO lien_ket_lich_bieu_nhan_vien (ma_nhan_vien, ma_lich_bieu)
                    VALUES (:ma_nhan_vien, :ma_lich_bieu)
                """),
                {
                    "ma_nhan_vien": ma_nhan_vien,
                    "ma_lich_bieu": ma_lich_bieu if ma_lich_bieu is not None else nhan_vien.ma_lich_bieu,
                }
            )
    
    await db.commit()
    
    return {"message": "Cập nhật thông tin nhân viên thành công!", "nhan_vien": {
        "ma_nhan_vien": ma_nhan_vien,
        "ho_ten": update_data["ho_ten"],
        "chuc_vu": chuc_vu if chuc_vu is not None else nhan_vien.chuc_vu,
        "ngay_sinh": update_data["ngay_sinh"],
        "dia_chi": update_data["dia_chi"],
        "email": update_data["email"],
        "dien_thoai": update_data["dien_thoai"],
        "skype": update_data["skype"],
        "zalo": update_data["zalo"],
        "facebook": update_data["facebook"],
        "ma_may_cham_cong": update_data["ma_may_cham_cong"],
        "cham_cong": update_data["cham_cong"],
        "trang_thai": update_data["trang_thai"],
        "noi_bat": update_data["noi_bat"],
        "ten_dang_nhap": update_data["ten_dang_nhap"],
        "ngay_vao_lam": ngay_vao_lam if ngay_vao_lam is not None else nhan_vien.ngay_vao_lam,
        "ngay_ky_hdld": ngay_ky_hdld if ngay_ky_hdld is not None else nhan_vien.ngay_ky_hdld,
        "ma_don_vi": ma_don_vi if ma_don_vi is not None else nhan_vien.ma_don_vi,
        "ma_loai_hop_dong": ma_loai_hop_dong if ma_loai_hop_dong is not None else nhan_vien.ma_loai_hop_dong,
        "ngay_bat_dau_hop_dong": ngay_bat_dau_hop_dong if ngay_bat_dau_hop_dong is not None else nhan_vien.ngay_bat_dau_hop_dong,
        "ngay_ket_thuc_hop_dong": ngay_ket_thuc_hop_dong if ngay_ket_thuc_hop_dong is not None else nhan_vien.ngay_ket_thuc_hop_dong,
        "ma_lich_bieu": ma_lich_bieu if ma_lich_bieu is not None else nhan_vien.ma_lich_bieu    
    }}

@router.put("/{ma_nhan_vien}/anh-dai-dien", status_code=200)
async def update_avatar_nhan_vien(
    ma_nhan_vien: int,
    file: UploadFile = File(),
    db: AsyncSession = Depends(deps.get_db_session),
    # user: UserInfo = Depends(verify_token),
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


# xóa nhân viên
@router.delete("/{ma_nhan_vien}", status_code=200)
async def delete_nhan_vien(
    ma_nhan_vien: int,
    db: AsyncSession = Depends(deps.get_db_session),
    user: UserInfo = Depends(verify_token)
):
    """
    Xóa nhân viên theo mã nhân viên.
    """
    if "admin" in user.roles or "executive" in user.roles:
        result = await db.execute(
            text("""SELECT 
                    nv.ma_nhan_vien,
                    dv.ma_don_vi,
                    lklhdnv.ma_loai_hop_dong,
                    lknvlb.ma_lich_bieu,
                    sdnp.ma_so_du
                FROM nhan_vien nv
                LEFT JOIN lien_ket_nhan_vien_don_vi lknvd ON nv.ma_nhan_vien = lknvd.ma_nhan_vien
                LEFT JOIN don_vi dv ON lknvd.ma_don_vi = dv.ma_don_vi
                LEFT JOIN lien_ket_loai_hop_dong_nhan_vien lklhdnv ON nv.ma_nhan_vien = lklhdnv.ma_nhan_vien
                LEFT JOIN lien_ket_lich_bieu_nhan_vien lknvlb ON nv.ma_nhan_vien = lknvlb.ma_nhan_vien
                LEFT JOIN so_du_nghi_phep sdnp ON nv.ma_nhan_vien = sdnp.ma_nhan_vien
                WHERE nv.ma_nhan_vien = :ma_nhan_vien"""),
            {"ma_nhan_vien": ma_nhan_vien}
        )
        nhan_vien = result.fetchone()

        if not nhan_vien:
            raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu nhân viên")

        if nhan_vien.ma_don_vi:
            # Xóa liên kết đơn vị
            await db.execute(
                text("DELETE FROM lien_ket_nhan_vien_don_vi WHERE ma_nhan_vien = :ma_nhan_vien"),
                {"ma_nhan_vien": ma_nhan_vien}
            )
        if nhan_vien.ma_loai_hop_dong:
            # Xóa liên kết loại hợp đồng
            await db.execute(
                text("DELETE FROM lien_ket_loai_hop_dong_nhan_vien WHERE ma_nhan_vien = :ma_nhan_vien"),
                {"ma_nhan_vien": ma_nhan_vien}
            )        
        
        if nhan_vien.ma_lich_bieu:
            # Xóa liên kết lịch biểu
            await db.execute(
                text("DELETE FROM lien_ket_lich_bieu_nhan_vien WHERE ma_nhan_vien = :ma_nhan_vien"),
                {"ma_nhan_vien": ma_nhan_vien}
            )
            
        if nhan_vien.ma_so_du:
            # Xóa số dư nghỉ phép
            await db.execute(
                text("DELETE FROM so_du_nghi_phep WHERE ma_nhan_vien = :ma_nhan_vien"),
                {"ma_nhan_vien": ma_nhan_vien}
            )
            
        # Xóa nhân viên
        await db.execute(
            text("DELETE FROM nhan_vien WHERE ma_nhan_vien = :ma_nhan_vien"),
            {"ma_nhan_vien": ma_nhan_vien}
        )

        await db.commit()

        return {"message": "Xóa nhân viên thành công!", "ma_nhan_vien": ma_nhan_vien}
    else:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa dữ liệu này.")