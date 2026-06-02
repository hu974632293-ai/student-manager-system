from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.teacher_service import TeacherService
from app.views.schemas.teacher import TeacherCreate, TeacherUpdate


teacher_router = APIRouter(prefix="/teacher", tags=["teacher"])


@teacher_router.post("/add")
def add_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    return TeacherService.create_teacher(db, teacher)


@teacher_router.get("/list")
def list_teachers(db: Session = Depends(get_db)):
    return TeacherService.list_teachers(db)


@teacher_router.get("/get/{teacher_id}")
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    return TeacherService.get_teacher(db, teacher_id)


@teacher_router.put("/update")
def update_teacher(teacher: TeacherUpdate, db: Session = Depends(get_db)):
    return TeacherService.update_teacher(db, teacher)


@teacher_router.delete("/delete/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    return TeacherService.delete_teacher(db, teacher_id)
