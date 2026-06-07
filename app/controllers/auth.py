from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_permissions_for_role
from app.services.auth_service import AuthService
from app.views.schemas.auth import ChangePasswordRequest, LoginRequest, LogoutRequest, RefreshTokenRequest


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


def require_permissions(*permissions: str):
    def dependency(user=Depends(get_current_user)):
        user_permissions = set(get_permissions_for_role(user.role))
        if permissions and not set(permissions).issubset(user_permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permission denied")
        return user

    return dependency


@auth_router.post("/login", summary="用户登录并获取访问令牌")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return AuthService.login(db, payload)


@auth_router.get("/me", summary="获取当前登录用户信息")
def me(user=Depends(get_current_user)):
    return AuthService.me(user)


@auth_router.post("/refresh", summary="刷新访问令牌")
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    return AuthService.refresh(db, payload)


@auth_router.post("/logout", summary="退出登录并撤销刷新令牌")
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    return AuthService.logout(db, payload)


@auth_router.post("/change-password", summary="修改当前用户密码")
def change_password(
    payload: ChangePasswordRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AuthService.change_password(db, user, payload)
