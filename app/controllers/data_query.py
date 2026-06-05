from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.auth import require_roles
from app.core.database import get_db
from app.services.data_query_service import DataQueryService
from app.views.schemas.data_query import DataQueryRequest


data_query_router = APIRouter(prefix="/data-query", tags=["data-query"])


@data_query_router.post("/nl2sql", summary="智能问数自然语言转 SQL")
def nl2sql(
    payload: DataQueryRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return DataQueryService.nl2sql(db, payload, current_user)
