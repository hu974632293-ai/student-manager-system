from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.services.student_service import StudentService
from app.views.schemas.student import StudentCommentRequest, StudentCreate


students_router = APIRouter()


@students_router.get("/students")
def get_allstudents(skip: int = 0, limit: int = 10, db=Depends(get_db)):
    return StudentService.list_students(db, skip=skip, limit=limit)


@students_router.get("/students/one")
def get_student(student_id=None, student_name=None, class_id=None, db=Depends(get_db)):
    return StudentService.get_student(db, student_id=student_id, student_name=student_name, class_id=class_id)


@students_router.post("/students")
def create_student(student: StudentCreate, db=Depends(get_db)):
    return StudentService.create_student(db, student)


@students_router.post("/students/comment")
def generate_student_comment(request: StudentCommentRequest, db=Depends(get_db)):
    return StudentService.generate_comment(db, request)


@students_router.put("/update_student/{student_id}")
def update_student(student_id: str, from_data: StudentCreate = Depends(), db=Depends(get_db)):
    return StudentService.update_student(db, student_id, from_data)


@students_router.post("/students_delete/")
def delete_student(student_id: int = None, student_name: str = None, db=Depends(get_db)):
    return StudentService.delete_student(db, student_id, student_name)
