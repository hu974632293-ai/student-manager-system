import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core import security
from app.dao.refresh_token import refresh_token_dao
from app.models.user import User


class TokenService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _build_refresh_token_data(user: User, created_ip=None, created_user_agent=None):
        plain_token = security.create_refresh_token_plaintext()
        jti = secrets.token_hex(32)
        return plain_token, {
            "user_id": user.id,
            "token_hash": security.hash_refresh_token(plain_token),
            "jti": jti,
            "expires_at": TokenService._now() + timedelta(days=security.JWT_REFRESH_EXPIRE_DAYS),
            "created_ip": created_ip,
            "created_user_agent": created_user_agent,
        }

    @staticmethod
    def issue_refresh_token(db: Session, user: User, created_ip=None, created_user_agent=None) -> str:
        plain_token, data = TokenService._build_refresh_token_data(user, created_ip, created_user_agent)
        try:
            row = refresh_token_dao.create(db, data)
            db.commit()
            db.refresh(row)
            return plain_token
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def rotate_refresh_token(db: Session, refresh_token: str):
        token_hash = security.hash_refresh_token(refresh_token)
        token = refresh_token_dao.get_by_hash(db, token_hash)
        now = TokenService._now()
        if not token or token.revoked_at is not None or token.expires_at <= now:
            return None

        user = db.query(User).filter(User.id == token.user_id, User.is_active == True).first()
        if not user:
            return None

        new_plain, new_data = TokenService._build_refresh_token_data(
            user,
            created_ip=token.created_ip,
            created_user_agent=token.created_user_agent,
        )
        try:
            refresh_token_dao.revoke(db, token, now, replaced_by_jti=new_data["jti"])
            new_token = refresh_token_dao.create(db, new_data)
            db.commit()
            db.refresh(new_token)
            return user, new_plain
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: str) -> bool:
        token_hash = security.hash_refresh_token(refresh_token)
        token = refresh_token_dao.get_by_hash(db, token_hash)
        if not token or token.revoked_at is not None:
            return False
        try:
            refresh_token_dao.revoke(db, token, TokenService._now())
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def revoke_all_for_user(db: Session, user_id: int):
        try:
            count = refresh_token_dao.revoke_all_for_user(db, user_id, TokenService._now())
            db.commit()
            return count
        except Exception:
            db.rollback()
            raise
