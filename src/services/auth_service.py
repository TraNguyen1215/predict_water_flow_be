from typing import Optional
from fastapi import HTTPException, status
from ..core.security import verify_password, get_password_hash, create_access_token
from ..repositories.user_repository import UserRepository
from ..schemas.user import UserCreate, UserLogin, Token


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def register_user(user_data: UserCreate) -> dict:
        """Register a new user."""
        existing_user = UserRepository.get_user_by_username(user_data.ten_dang_nhap)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên đăng nhập đã tồn tại"
            )
        
        if user_data.email:
            existing_email = UserRepository.get_user_by_email(user_data.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email đã được sử dụng"
                )
        
        hashed_password = get_password_hash(user_data.mat_khau)
        
        user_dict = user_data.model_dump()
        user_dict['mat_khau'] = hashed_password
        
        new_user = UserRepository.create_user(user_dict)
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể tạo tài khoản"
            )
        
        return new_user
    
    @staticmethod
    def login_user(login_data: UserLogin) -> Token:
        """Login user and return access token."""
        user = UserRepository.get_user_by_username(login_data.ten_dang_nhap)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên đăng nhập hoặc mật khẩu không đúng",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.get('trang_thai'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đã bị vô hiệu hóa"
            )
        
        if not verify_password(login_data.mat_khau, user['mat_khau']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên đăng nhập hoặc mật khẩu không đúng",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            data={"sub": str(user['id']), "username": user['ten_dang_nhap']}
        )
        
        return Token(access_token=access_token, token_type="bearer")
    
    @staticmethod
    def get_current_user_data(user_id: int) -> dict:
        """Get current user data."""
        user = UserRepository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Người dùng không tồn tại"
            )
        
        user.pop('mat_khau', None)
        return user
