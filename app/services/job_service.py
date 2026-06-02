from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.dao import jobs as job_dao
from app.views.schemas.jobs import StudentJobCreate


class JobService:
    @staticmethod
    def create_job(db: Session, job_in: StudentJobCreate):
        if not job_dao.student_exists(db, job_in.student_id):
            return fail(f"student_id {job_in.student_id} does not exist")
        job = job_dao.create_student_job(db, job_in.model_dump())
        return success(job, "job created")

    @staticmethod
    def get_job(db: Session, student_id: str):
        jobs = job_dao.query_student_id(db, student_id)
        return success(jobs, "jobs found")

    @staticmethod
    def get_class_jobs(db: Session, class_name: str):
        return success(job_dao.get_student_jobs_by_class(db, class_name), "jobs found")

    @staticmethod
    def get_jobs_by_salary_range(db: Session, min_salary=None, max_salary=None):
        return success(
            job_dao.get_jobs_by_salary_range(db=db, min_salary=min_salary, max_salary=max_salary),
            "jobs found",
        )

    @staticmethod
    def update_job(db: Session, job_id: int, job_in: StudentJobCreate):
        job = job_dao.update_student_job(db, job_id, job_in.model_dump(exclude_unset=True))
        if not job:
            return fail("job record not found")
        return success(job, "job updated")

    @staticmethod
    def delete_job(db: Session, student_id: str):
        deleted = job_dao.delete_student_job_by_student_id(db, student_id)
        if not deleted:
            return fail("job record not found")
        return success({"student_id": student_id}, "job deleted")

    @staticmethod
    def get_job_page(db: Session, page: int, size: int):
        return success(job_dao.get_job_page(db=db, page=page, size=size), "jobs found")
