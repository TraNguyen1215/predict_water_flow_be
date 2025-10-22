import pytest
from src.core import security
from datetime import timedelta


def test_password_hash_and_verify():
    pwd = "secret123"
    hashed, salt = security.get_password_hash_and_salt(pwd)
    assert hashed != pwd
    assert security.verify_password(pwd, salt, hashed)
    assert not security.verify_password("wrong", salt, hashed)


def test_jwt_create_and_decode():
    data = {"sub": "1234"}
    token = security.create_access_token(data, expires_delta=timedelta(minutes=1))
    payload = security.decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "1234"