from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.dao.teacher import teacher_dao
from app.views.schemas.teacher import TeacherCreate, TeacherUpdate


class TeacherService:
    @staticmethod
    def create_teacher(db: Session, teacher: TeacherCreate):
        return success(teacher_dao.create_teacher(db, teacher.model_dump()), "teacher created")

    @staticmethod
    def list_teachers(db: Session):
        return success(teacher_dao.get_all_teachers(db), "teachers found")

    @staticmethod
    def get_teacher(db: Session, teacher_id: int):
        teacher = teacher_dao.get_teacher_by_id(db, teacher_id)
        if not teacher:
            return fail("teacher not found")
        return success(teacher, "teacher found")

    @staticmethod
    def update_teacher(db: Session, teacher: TeacherUpdate):
        updated = teacher_dao.update_teacher(db, teacher.id, teacher.model_dump(exclude_unset=True))
        if not updated:
            return fail("teacher not found")
        return success(updated, "teacher updated")

    @staticmethod
    def delete_teacher(db: Session, teacher_id: int):
        if not teacher_dao.delete_teacher(db, teacher_id):
            return fail("teacher not found")
        return success(None, "teacher deleted")
