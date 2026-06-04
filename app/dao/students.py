from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import or_

from app.models.student import Student


def _apply_student_scope(query, student_ids=None, class_ids=None, consultant_id=None):
    if student_ids is not None:
        if not student_ids:
            return query.filter(False)
        query = query.filter(Student.student_id.in_(student_ids))
    if class_ids is not None:
        if not class_ids:
            return query.filter(False)
        query = query.filter(Student.class_id.in_(class_ids))
    if consultant_id is not None:
        query = query.filter(Student.consultant_id == consultant_id)
    return query


def get_allstudents(db: Session, skip: int = 0, limit: int = 10, student_ids=None, class_ids=None, consultant_id=None):
    query = db.query(Student).filter(Student.is_deleted == False).order_by(Student.student_id.asc())
    query = _apply_student_scope(query, student_ids=student_ids, class_ids=class_ids, consultant_id=consultant_id)
    return query.offset(skip).limit(limit).all(), query.count()


def get_student(db: Session, student_id=None, student_name=None, class_id=None, student_ids=None, class_ids=None, consultant_id=None):
    select_id = None
    select_name = None
    select_class = []
    if student_id not in (None, ""):
        query = db.query(Student).filter(Student.student_id == student_id, Student.is_deleted == False)
        select_id = _apply_student_scope(query, student_ids=student_ids, class_ids=class_ids, consultant_id=consultant_id).first()
    if student_name not in (None, ""):
        query = db.query(Student).filter(Student.name == student_name, Student.is_deleted == False)
        select_name = _apply_student_scope(query, student_ids=student_ids, class_ids=class_ids, consultant_id=consultant_id).first()
    if class_id not in (None, ""):
        query = db.query(Student).filter(Student.class_id == class_id, Student.is_deleted == False)
        select_class = _apply_student_scope(query, student_ids=student_ids, class_ids=class_ids, consultant_id=consultant_id).all()
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
