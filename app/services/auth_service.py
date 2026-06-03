import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.database import Base, engine, get_db
from app.core.response import fail, success
from app.models.user import User
from app.views.schemas.auth import LoginRequest, LoginResponse


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "wolinsms-dev-secret")
TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "8"))


class AuthService:
    @staticmethod
    def _b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    @staticmethod
    def _b64url_decode(data: str) -> bytes:
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 120000)
        return f"pbkdf2_sha256${salt}${digest.hex()}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            algorithm, salt, stored = password_hash.split("$", 2)
        except ValueError:
            return False
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 120000)
        return hmac.compare_digest(digest.hex(), stored)

    @staticmethod
    def create_access_token(user: User) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user.username,
            "uid": user.id,
            "role": user.role,
            "name": user.real_name,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=TOKEN_EXPIRE_HOURS)).timestamp()),
        }
        header = {"alg": "HS256", "typ": "JWT"}
        signing_input = (
            f"{AuthService._b64url_encode(json.dumps(header, separators=(',', ':')).encode())}."
            f"{AuthService._b64url_encode(json.dumps(payload, separators=(',', ':')).encode())}"
        )
        signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        return f"{signing_input}.{AuthService._b64url_encode(signature)}"

    @staticmethod
    def decode_access_token(token: str):
        try:
            header_b64, payload_b64, signature_b64 = token.split(".")
            signing_input = f"{header_b64}.{payload_b64}"
            expected = hmac.new(SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
            if not hmac.compare_digest(AuthService._b64url_encode(expected), signature_b64):
                return None
            payload = json.loads(AuthService._b64url_decode(payload_b64))
            if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
                return None
            return payload
        except Exception:
            return None

    @staticmethod
    def get_current_user(db: Session, authorization: str | None):
        if not authorization or not authorization.lower().startswith("bearer "):
            return None
        payload = AuthService.decode_access_token(authorization.split(" ", 1)[1])
        if not payload:
            return None
        return db.query(User).filter(User.username == payload["sub"], User.is_active == True).first()

    @staticmethod
    def ensure_default_users() -> None:
        for attempt in range(5):
            try:
                AuthService._ensure_default_users_once()
                return
            except OperationalError:
                if attempt == 4:
                    raise
                time.sleep(2)

    @staticmethod
    def _ensure_default_users_once() -> None:
        Base.metadata.create_all(bind=engine)
        defaults = [
            ("admin", "admin123", "System Admin", "admin"),
            ("teacher", "teacher123", "Demo Teacher", "teacher"),
            ("consultant", "consultant123", "Consultant", "consultant"),
        ]
        db = next(get_db())
        try:
            for username, password, real_name, role in defaults:
                if not db.query(User).filter(User.username == username).first():
                    db.add(
                        User(
                            username=username,
                            password_hash=AuthService.hash_password(password),
                            real_name=real_name,
                            role=role,
                        )
                    )
            db.commit()
        finally:
            db.close()

    @staticmethod
    def login(db: Session, payload: LoginRequest):
        user = db.query(User).filter(User.username == payload.username, User.is_active == True).first()
        if not user or not AuthService.verify_password(payload.password, user.password_hash):
            return fail("bad username or password")
        return success(LoginResponse(access_token=AuthService.create_access_token(user), user=user), "login success")

    @staticmethod
    def me(user: User):
        return success(user, "current user")
