from typing import Optional

from sqlalchemy.orm import Session

from app.models.job import StudentJob
from app.models.student import Student


def student_exists(db: Session, student_id: str) -> bool:
    return db.query(Student.id).filter(Student.student_id == student_id).first() is not None


def query_student_id(db: Session, student_id: str):
    return db.query(StudentJob).filter(StudentJob.student_id == student_id).all()


def get_student_jobs_by_class(db: Session, class_name: str):
    return db.query(StudentJob).filter(StudentJob.class_name == class_name).all()


def get_job_by_id(db: Session, job_id: int):
    return db.query(StudentJob).filter(StudentJob.id == job_id).first()


def update_student_job(db: Session, job_id: int, job_data: dict):
    job = get_job_by_id(db, job_id)
    if not job:
        return None
    for key, value in job_data.items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


def create_student_job(db: Session, job_data: dict):
    job = StudentJob(**job_data)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_jobs_by_salary_range(db: Session, min_salary: Optional[float] = None, max_salary: Optional[float] = None):
    query = db.query(StudentJob)
    if min_salary is not None:
        query = query.filter(StudentJob.salary >= min_salary)
    if max_salary is not None:
        query = query.filter(StudentJob.salary <= max_salary)
    return query.order_by(StudentJob.salary.desc()).all()


def delete_student_job_by_student_id(db: Session, student_id: str) -> int:
    deleted = db.query(StudentJob).filter(StudentJob.student_id == student_id).delete()
    db.commit()
    return deleted


def get_job_page(db: Session, page: int, size: int):
    query = db.query(StudentJob).order_by(StudentJob.salary.desc())
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {"total": total, "page": page, "size": size, "list": items}
