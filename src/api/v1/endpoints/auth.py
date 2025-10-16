from fastapi import APIRouter, Depends, HTTPException, status
from ....schemas.user import UserCreate, UserLogin, UserResponse, Token
from ....services.auth_service import AuthService
from ...dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Đăng ký tài khoản mới.
    
    - **ten_dang_nhap**: Tên đăng nhập (bắt buộc, 3-50 ký tự)
    - **mat_khau**: Mật khẩu (bắt buộc, tối thiểu 6 ký tự)
    - **ho_ten**: Họ và tên (bắt buộc, 2-100 ký tự)
    - **email**: Email (tùy chọn)
    - **sdt**: Số điện thoại (tùy chọn)
    - **dia_chi**: Địa chỉ (tùy chọn)
    """
    user = AuthService.register_user(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """
    Đăng nhập vào hệ thống.
    
    - **ten_dang_nhap**: Tên đăng nhập
    - **mat_khau**: Mật khẩu
    
    Trả về access token để sử dụng cho các API khác.
    """
    token = AuthService.login_user(login_data)
    return token


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Lấy thông tin người dùng hiện tại.
    
    Yêu cầu: Bearer Token trong header Authorization
    """
    return current_user


@router.get("/test-protected")
async def test_protected_route(current_user: dict = Depends(get_current_user)):
    """
    Route test để kiểm tra authentication.
    
    Yêu cầu: Bearer Token trong header Authorization
    """
    return {
        "message": "Bạn đã xác thực thành công!",
        "user": current_user
    }
