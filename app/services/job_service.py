from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.dao import jobs as job_dao
from app.services.access_scope_service import AccessScopeService
from app.views.schemas.jobs import StudentJobCreate


class JobService:
    @staticmethod
    def _scope_kwargs(db: Session, current_user=None) -> dict:
        if current_user is None or AccessScopeService.is_admin(current_user):
            return {}
        class_names = AccessScopeService.teacher_class_names(db, current_user) if current_user.role == "teacher" else None
        return {
            "allowed_student_ids": AccessScopeService.allowed_student_ids(db, current_user),
            "class_names": class_names,
        }

    @staticmethod
    def create_job(db: Session, job_in: StudentJobCreate, current_user=None):
        if current_user is not None and not AccessScopeService.can_access_student(db, current_user, job_in.student_id):
            return fail("permission denied")
        if not job_dao.student_exists(db, job_in.student_id):
            return fail(f"student_id {job_in.student_id} does not exist")
        job = job_dao.create_student_job(db, job_in.model_dump())
        return success(job, "job created")

    @staticmethod
    def get_job(db: Session, student_id: str, current_user=None):
        jobs = job_dao.query_student_id(db, student_id, **JobService._scope_kwargs(db, current_user))
        return success(jobs, "jobs found")

    @staticmethod
    def get_class_jobs(db: Session, class_name: str, current_user=None):
        return success(job_dao.get_student_jobs_by_class(db, class_name, **JobService._scope_kwargs(db, current_user)), "jobs found")

    @staticmethod
    def get_jobs_by_salary_range(db: Session, min_salary=None, max_salary=None, current_user=None):
        return success(
            job_dao.get_jobs_by_salary_range(
                db=db,
                min_salary=min_salary,
                max_salary=max_salary,
                **JobService._scope_kwargs(db, current_user),
            ),
            "jobs found",
        )

    @staticmethod
    def update_job(db: Session, job_id: int, job_in: StudentJobCreate, current_user=None):
        if current_user is not None and not AccessScopeService.can_access_student(db, current_user, job_in.student_id):
            return fail("permission denied")
        job = job_dao.update_student_job(db, job_id, job_in.model_dump(exclude_unset=True))
        if not job:
            return fail("job record not found")
        return success(job, "job updated")

    @staticmethod
    def delete_job(db: Session, student_id: str, current_user=None):
        if current_user is not None and not AccessScopeService.can_access_student(db, current_user, student_id):
            return fail("permission denied")
        deleted = job_dao.delete_student_job_by_student_id(db, student_id)
        if not deleted:
            return fail("job record not found")
        return success({"student_id": student_id}, "job deleted")

    @staticmethod
    def get_job_page(db: Session, page: int, size: int, current_user=None):
        return success(job_dao.get_job_page(db=db, page=page, size=size, **JobService._scope_kwargs(db, current_user)), "jobs found")
