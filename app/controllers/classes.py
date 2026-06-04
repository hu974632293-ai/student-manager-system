from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.controllers.auth import require_roles
from app.services.class_service import ClassService
from app.views.schemas.classes import ClassCreate, ClassUpdate


class_router = APIRouter(prefix="/classes", tags=["classes"])


@class_router.post("/", summary="新增班级信息")
def create_class(
    class_in: ClassCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    return ClassService.create_class(db, class_in)


@class_router.get("/", summary="分页查询班级列表")
def list_classes(
    page: int = 1,
    size: int = 10,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return ClassService.list_classes(db, page, size, keyword, current_user=current_user)


@class_router.get("/{class_id}", summary="查询指定班级详情")
def get_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return ClassService.get_class(db, class_id, current_user=current_user)


@class_router.put("/", summary="更新班级信息")
def update_class(
    class_in: ClassUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    return ClassService.update_class(db, class_in)


@class_router.delete("/{class_id}", summary="删除指定班级")
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    return ClassService.delete_class(db, class_id)
