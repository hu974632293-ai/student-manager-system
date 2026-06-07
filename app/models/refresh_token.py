from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.database import Base


class UserRefreshToken(Base):
    __tablename__ = "user_refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    jti = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    replaced_by_jti = Column(String(64), nullable=True)
    created_ip = Column(String(64), nullable=True)
    created_user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
