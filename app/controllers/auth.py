from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.views.schemas.auth import LoginRequest


auth_router = APIRouter(prefix="/auth", tags=["auth"])


def ensure_default_users() -> None:
    AuthService.ensure_default_users()


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    user = AuthService.get_current_user(db, authorization)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="login required")
    return user


def require_roles(*roles: str):
    def dependency(user=Depends(get_current_user)):
        if roles and user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permission denied")
        return user

    return dependency


@auth_router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return AuthService.login(db, payload)


@auth_router.get("/me")
def me(user=Depends(get_current_user)):
    return AuthService.me(user)
