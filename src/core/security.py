from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import jwt, JWTError
import os
import hashlib
import binascii
import hmac
from .config import settings

# PBKDF2 settings
PBKDF2_ITERATIONS = 100_000
SALT_SIZE = 16  # bytes


def generate_salt() -> str:
    """Return a new random salt as a hex string."""
    return binascii.hexlify(os.urandom(SALT_SIZE)).decode()


def hash_password(password: str, salt_hex: str) -> str:
    """Hash a password with the provided salt (hex) and return hex digest."""
    salt = binascii.unhexlify(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return binascii.hexlify(dk).decode()


def get_password_hash_and_salt(password: str) -> Tuple[str, str]:
    """Generate a salt and return (hash_hex, salt_hex)."""
    salt = generate_salt()
    hashed = hash_password(password, salt)
    return hashed, salt


def verify_password(plain_password: str, salt_hex: str, hashed_password_hex: str) -> bool:
    """Verify a password using stored salt and hash (both hex strings)."""
    computed = hash_password(plain_password, salt_hex)
    # Use constant-time comparison
    return hmac.compare_digest(computed, hashed_password_hex)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
