from fastapi import APIRouter, Depends, Query

from app.controllers.auth import require_roles
from app.services.log_service import LogService


logs_router = APIRouter(prefix="/logs", tags=["logs"])


@logs_router.get("/recent", summary="查询最近系统日志")
def list_recent_logs(
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(require_roles("admin")),
):
    return LogService.list_recent_logs(limit)
