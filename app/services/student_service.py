from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.dao import students as student_dao
from app.views.schemas.student import StudentCreate


class StudentService:
    @staticmethod
    def list_students(db: Session, skip: int = 0, limit: int = 10):
        students, total = student_dao.get_allstudents(db, skip=skip, limit=limit)
        return success({"total": total, "students": students}, "students found")

    @staticmethod
    def get_student(db: Session, student_id=None, student_name=None, class_id=None):
        select_id, select_name, select_class = student_dao.get_student(
            db,
            student_id=student_id,
            student_name=student_name,
            class_id=class_id,
        )
        return success(
            {
                "select_id": select_id,
                "select_name": select_name,
                "class_id": select_class,
            },
            "student found",
        )

    @staticmethod
    def create_student(db: Session, student: StudentCreate):
        data = student.model_dump()
        data["is_deleted"] = False
        if data.get("consultant_id") in (0, None):
            data.pop("consultant_id", None)
        try:
            return success(student_dao.create_student(db, data), "student created")
        except ValueError as exc:
            return fail(str(exc))

    @staticmethod
    def update_student(db: Session, student_id: str, student: StudentCreate):
        update_data = student.model_dump(exclude_unset=True)
        update_data.pop("student_id", None)
        update_data.pop("is_deleted", None)
        updated = student_dao.update_student(db, student_id, update_data)
        if not updated:
            return fail("student not found")
        return success(updated, "student updated")

    @staticmethod
    def delete_student(db: Session, student_id: int = None, student_name: str = None):
        deleted = student_dao.delete_student(db, student_id, student_name)
        if not deleted:
            return fail("student not found")
        return success(deleted, "student deleted")
