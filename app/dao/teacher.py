from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.teacher import Teacher


class TeacherDao:
    def get_all_teachers(self, db: Session):
        return db.query(Teacher).filter(Teacher.is_deleted == False).all()

    def get_teacher_by_id(self, db: Session, teacher_id: int):
        return db.query(Teacher).filter(Teacher.id == teacher_id, Teacher.is_deleted == False).first()

    def create_teacher(self, db: Session, teacher_data: dict):
        teacher = Teacher(**teacher_data)
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        return teacher

    def update_teacher(self, db: Session, teacher_id: int, teacher_data: dict):
        teacher = self.get_teacher_by_id(db, teacher_id)
        if not teacher:
            return None
        teacher_data.pop("id", None)
        for key, value in teacher_data.items():
            if key != "id":
                setattr(teacher, key, value)
        db.commit()
        db.refresh(teacher)
        return teacher

    def delete_teacher(self, db: Session, teacher_id: int):
        teacher = self.get_teacher_by_id(db, teacher_id)
        if not teacher:
            return False
        teacher.is_deleted = True
        try:
            db.commit()
            return True
        except SQLAlchemyError:
            db.rollback()
            return False


teacher_dao = TeacherDao()
