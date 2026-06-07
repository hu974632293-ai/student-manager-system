from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.core import security


def make_user(**overrides):
    data = {
        "id": 1,
        "username": "admin",
        "real_name": "System Admin",
        "role": "admin",
        "teacher_id": None,
        "student_id": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_password_hash_roundtrip():
    password_hash = security.hash_password("admin123")

    assert password_hash.startswith("pbkdf2_sha256$")
    assert security.verify_password("admin123", password_hash) is True
    assert security.verify_password("wrong", password_hash) is False


def test_access_token_contains_user_identity():
    token = security.create_access_token(make_user())

    payload = security.decode_access_token(token)

    assert payload["sub"] == "admin"
    assert payload["uid"] == 1
    assert payload["role"] == "admin"
    assert payload["jti"]


def test_expired_access_token_returns_none():
    token = security.create_access_token(
        make_user(),
        expires_delta=timedelta(seconds=-1),
        now=datetime.now(timezone.utc),
    )

    assert security.decode_access_token(token) is None
