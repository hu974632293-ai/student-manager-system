from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.job_service import JobService
from app.views.schemas.jobs import StudentJobCreate


router_job = APIRouter()


@router_job.post("/employment/students/add")
def create_job(job_data: StudentJobCreate, db: Session = Depends(get_db)):
    return JobService.create_job(db, job_data)


@router_job.get("/jobs/salary-range")
def get_jobs(min_salary: Optional[float] = Query(None), max_salary: Optional[float] = Query(None), db: Session = Depends(get_db)):
    return JobService.get_jobs_by_salary_range(db=db, min_salary=min_salary, max_salary=max_salary)


@router_job.get("/employment/students/{student_id}")
def get_student_job(student_id: str, db: Session = Depends(get_db)):
    return JobService.get_job(db, student_id)


@router_job.get("/employment/class/{class_name}")
def get_class_jobs(class_name: str, db: Session = Depends(get_db)):
    return JobService.get_class_jobs(db, class_name)


@router_job.post("/employment/students/{job_id}")
def update_job(job_id: int, job_data: StudentJobCreate, db: Session = Depends(get_db)):
    return JobService.update_job(db, job_id, job_data)


@router_job.delete("/employment/students/by-student-id/{student_id}")
def delete_job_by_student_id(student_id: str, db: Session = Depends(get_db)):
    return JobService.delete_job(db, student_id)


@router_job.get("/jobs/page")
def get_job_page_api(page: int = Query(1), size: int = Query(10), db: Session = Depends(get_db)):
    return JobService.get_job_page(db=db, page=page, size=size)
