from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import or_

from app.models.student import Student


def get_allstudents(db: Session, skip: int = 0, limit: int = 10):
    query = db.query(Student).filter(Student.is_deleted == False).order_by(Student.student_id.asc())
    return query.offset(skip).limit(limit).all(), query.count()


def get_student(db: Session, student_id=None, student_name=None, class_id=None):
    select_id = None
    select_name = None
    select_class = []
    if student_id not in (None, ""):
        select_id = db.query(Student).filter(Student.student_id == student_id, Student.is_deleted == False).first()
    if student_name not in (None, ""):
        select_name = db.query(Student).filter(Student.name == student_name, Student.is_deleted == False).first()
    if class_id not in (None, ""):
        select_class = db.query(Student).filter(Student.class_id == class_id, Student.is_deleted == False).all()
    return select_id, select_name, select_class


def get_student_by_student_id(db: Session, student_id: str):
    return db.query(Student).filter(Student.student_id == student_id, Student.is_deleted == False).first()


def create_student(db: Session, student_data: dict):
    for field in ["student_id", "class_id", "name"]:
        if not student_data.get(field):
            raise ValueError(f"field {field} is required")
    exists = db.query(Student).filter(Student.student_id == student_data["student_id"]).first()
    if exists:
        raise ValueError(f"student_id {student_data['student_id']} already exists")
    student = Student(**student_data)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def update_student(db: Session, student_id: int, update_data: dict):
    student = db.query(Student).filter(Student.student_id == student_id, Student.is_deleted == False).first()
    if not student:
        return None
    for key, value in update_data.items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student_id: int = None, student_name: str = None):
    student = db.query(Student).filter(or_(Student.student_id == student_id, Student.name == student_name)).first()
    if not student:
        return None
    student.is_deleted = True
    db.commit()
    db.refresh(student)
    return student
