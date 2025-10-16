from typing import Optional, List
from ..db.database import execute_query, execute_one
from ..models.user import User


class UserRepository:
    """Repository for user database operations."""
    
    @staticmethod
    def create_user(user_data: dict) -> Optional[dict]:
        """Create a new user in the database."""
        query = """
            INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, ho_ten, email, sdt, dia_chi, vai_tro)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, ten_dang_nhap, ho_ten, email, sdt, dia_chi, vai_tro, trang_thai, ngay_tao, ngay_cap_nhat
        """
        params = (
            user_data['ten_dang_nhap'],
            user_data['mat_khau'],
            user_data['ho_ten'],
            user_data.get('email'),
            user_data.get('sdt'),
            user_data.get('dia_chi'),
            user_data.get('vai_tro', 'user')
        )
        result = execute_one(query, params)
        return dict(result) if result else None
    
    @staticmethod
    def get_user_by_username(ten_dang_nhap: str) -> Optional[dict]:
        """Get a user by username."""
        query = """
            SELECT id, ten_dang_nhap, mat_khau, ho_ten, email, sdt, dia_chi, vai_tro, trang_thai, ngay_tao, ngay_cap_nhat
            FROM nguoi_dung
            WHERE ten_dang_nhap = %s
        """
        result = execute_one(query, (ten_dang_nhap,))
        return dict(result) if result else None
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[dict]:
        """Get a user by ID."""
        query = """
            SELECT id, ten_dang_nhap, mat_khau, ho_ten, email, sdt, dia_chi, vai_tro, trang_thai, ngay_tao, ngay_cap_nhat
            FROM nguoi_dung
            WHERE id = %s
        """
        result = execute_one(query, (user_id,))
        return dict(result) if result else None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[dict]:
        """Get a user by email."""
        query = """
            SELECT id, ten_dang_nhap, mat_khau, ho_ten, email, sdt, dia_chi, vai_tro, trang_thai, ngay_tao, ngay_cap_nhat
            FROM nguoi_dung
            WHERE email = %s
        """
        result = execute_one(query, (email,))
        return dict(result) if result else None
    
    @staticmethod
    def get_all_users() -> List[dict]:
        """Get all users."""
        query = """
            SELECT id, ten_dang_nhap, ho_ten, email, sdt, dia_chi, vai_tro, trang_thai, ngay_tao, ngay_cap_nhat
            FROM nguoi_dung
            ORDER BY ngay_tao DESC
        """
        results = execute_query(query)
        return [dict(row) for row in results] if results else []
    
    @staticmethod
    def update_user(user_id: int, user_data: dict) -> Optional[dict]:
        """Update a user."""
        update_fields = []
        params = []
        
        for key, value in user_data.items():
            if value is not None:
                update_fields.append(f"{key} = %s")
                params.append(value)
        
        if not update_fields:
            return None
        
        params.append(user_id)
        query = f"""
            UPDATE nguoi_dung
            SET {', '.join(update_fields)}, ngay_cap_nhat = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, ten_dang_nhap, ho_ten, email, sdt, dia_chi, vai_tro, trang_thai, ngay_tao, ngay_cap_nhat
        """
        result = execute_one(query, tuple(params))
        return dict(result) if result else None
    
    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Delete a user (soft delete by setting trang_thai to False)."""
        query = """
            UPDATE nguoi_dung
            SET trang_thai = FALSE, ngay_cap_nhat = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """
        result = execute_one(query, (user_id,))
        return result is not None
