import hmac
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_permissions_for_role
from app.models.user import User
from app.services.dify_gateway_service import DifyGatewayService
from app.views.schemas.dify_gateway import DifyStudentQueryRequest


dify_gateway_router = APIRouter(prefix="/dify-gateway", tags=["dify-gateway"])


def _configured_gateway_token() -> str | None:
    return os.getenv("DIFY_GATEWAY_API_KEY") or os.getenv("DIFY_GATEWAY_TOKEN")


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def require_dify_gateway_token(
    x_dify_token: Optional[str] = Header(None, alias="X-Dify-Token"),
    authorization: Optional[str] = Header(None),
) -> None:
    expected = _configured_gateway_token()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dify gateway token not configured",
        )
    provided = (x_dify_token or "").strip() or _extract_bearer_token(authorization)
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Dify gateway token invalid")


def get_dify_gateway_user(
    db: Session = Depends(get_db),
    _=Depends(require_dify_gateway_token),
):
    username = os.getenv("DIFY_GATEWAY_USERNAME", "admin").strip()
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dify gateway user not found")
    return user


def require_dify_permissions(*permissions: str):
    def dependency(user=Depends(get_dify_gateway_user)):
        user_permissions = set(get_permissions_for_role(user.role))
        if permissions and not set(permissions).issubset(user_permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permission denied")
        return user

    return dependency


@dify_gateway_router.post("/students/query", summary="Dify 查询学生信息")
def query_students_for_dify(
    payload: DifyStudentQueryRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_dify_permissions("students:read")),
):
    return DifyGatewayService.query_students(db, payload, current_user)
