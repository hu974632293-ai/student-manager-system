from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.controllers.auth import require_roles
from app.services.teacher_service import TeacherService
from app.views.schemas.teacher import TeacherCreate, TeacherUpdate


teacher_router = APIRouter(prefix="/teacher", tags=["teacher"])


@teacher_router.post("/add", summary="新增教师信息")
def add_teacher(
    teacher: TeacherCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    return TeacherService.create_teacher(db, teacher)


@teacher_router.get("/list", summary="查询教师列表")
def list_teachers(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return TeacherService.list_teachers(db)


@teacher_router.get("/get/{teacher_id}", summary="查询指定教师详情")
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return TeacherService.get_teacher(db, teacher_id)


@teacher_router.put("/update", summary="更新教师信息")
def update_teacher(
    teacher: TeacherUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    return TeacherService.update_teacher(db, teacher)


@teacher_router.delete("/delete/{teacher_id}", summary="删除指定教师")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    return TeacherService.delete_teacher(db, teacher_id)
