from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.classes import Class
from app.models.job import StudentJob
from app.models.score import StudentScore
from app.models.student import Student
from app.models.teacher import Teacher


class StatisticsDao:
    def _clean_optional_text(self, value: Optional[str]):
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    def _filter_class(self, query, class_id: Optional[str]):
        class_id = self._clean_optional_text(class_id)
        if not class_id:
            return query
        filters = [Class.class_id == class_id]
        if class_id.isdigit():
            filters.append(Class.id == int(class_id))
        return query.filter(*filters) if len(filters) == 1 else query.filter((Class.class_id == class_id) | (Class.id == int(class_id)))

    def _filter_student_ids(self, query, allowed_student_ids: Optional[list[str]]):
        if allowed_student_ids is None:
            return query
        if not allowed_student_ids:
            return query.filter(False)
        return query.filter(Student.student_id.in_(allowed_student_ids))

    def _filter_job_student_ids(self, query, allowed_student_ids: Optional[list[str]]):
        if allowed_student_ids is None:
            return query
        if not allowed_student_ids:
            return query.filter(False)
        return query.filter(StudentJob.student_id.in_(allowed_student_ids))

    def get_students_over_30(self, db: Session, min_age: int = 30, allowed_student_ids: Optional[list[str]] = None):
        query = db.query(Student).filter(Student.is_deleted == False, Student.age > min_age)
        return self._filter_student_ids(query, allowed_student_ids).all()

    def get_class_gender_counts(self, db: Session, class_id: Optional[str] = None, allowed_student_ids: Optional[list[str]] = None):
        query = db.query(
            Class.class_id.label("class_id"),
            func.count(Student.id).label("total_count"),
            func.sum(case((Student.gender == "\u7537", 1), else_=0)).label("male_count"),
            func.sum(case((Student.gender == "\u5973", 1), else_=0)).label("female_count"),
        ).join(Student, Student.class_id == Class.id).filter(Class.is_deleted == False, Student.is_deleted == False)
        query = self._filter_student_ids(query, allowed_student_ids)
        class_id = self._clean_optional_text(class_id)
        if class_id:
            if class_id.isdigit():
                query = query.filter((Class.id == int(class_id)) | (Class.class_id == class_id))
            else:
                query = query.filter(Class.class_id == class_id)
        return query.group_by(Class.class_id).all()

    def get_students_all_scores_above_80(self, db: Session, min_score: float = 80, allowed_student_ids: Optional[list[str]] = None):
        subquery = db.query(StudentScore.student_id)
        if allowed_student_ids is not None:
            if not allowed_student_ids:
                return []
            subquery = subquery.filter(StudentScore.student_id.in_(allowed_student_ids))
        subquery = subquery.group_by(StudentScore.student_id).having(func.min(StudentScore.score) >= min_score).subquery()
        query = db.query(Student.student_id, Student.name, StudentScore.exam_round, StudentScore.score).join(
            StudentScore, Student.student_id == StudentScore.student_id
        ).filter(Student.student_id.in_(subquery))
        return self._filter_student_ids(query, allowed_student_ids).all()

    def get_students_failed_more_than_twice(self, db: Session, fail_score: float = 60, min_fail_count: int = 2, allowed_student_ids: Optional[list[str]] = None):
        failed = db.query(StudentScore.student_id).filter(StudentScore.score < fail_score)
        if allowed_student_ids is not None:
            if not allowed_student_ids:
                return []
            failed = failed.filter(StudentScore.student_id.in_(allowed_student_ids))
        failed = failed.group_by(StudentScore.student_id).having(
            func.count(StudentScore.id) > min_fail_count
        ).subquery()
        query = db.query(Student.name, Class.class_id, StudentScore.exam_round, StudentScore.score).join(
            StudentScore, Student.student_id == StudentScore.student_id
        ).join(Class, Student.class_id == Class.id).filter(Student.student_id.in_(failed), StudentScore.score < fail_score)
        return self._filter_student_ids(query, allowed_student_ids).all()

    def get_exam_class_average_scores(self, db: Session, class_id: Optional[str] = None, exam_round: Optional[int] = None, allowed_student_ids: Optional[list[str]] = None):
        query = db.query(
            StudentScore.exam_round,
            Class.class_id.label("class_id"),
            func.avg(StudentScore.score).label("average_score"),
        ).join(Student, StudentScore.student_id == Student.student_id).join(Class, Student.class_id == Class.id)
        query = self._filter_student_ids(query, allowed_student_ids)
        class_id = self._clean_optional_text(class_id)
        if class_id:
            if class_id.isdigit():
                query = query.filter((Class.id == int(class_id)) | (Class.class_id == class_id))
            else:
                query = query.filter(Class.class_id == class_id)
        if exam_round is not None:
            query = query.filter(StudentScore.exam_round == exam_round)
        return query.group_by(StudentScore.exam_round, Class.class_id).all()

    def get_top5_salary_students(self, db: Session, limit: int = 5, allowed_student_ids: Optional[list[str]] = None):
        query = db.query(
            StudentJob.name,
            StudentJob.class_name,
            StudentJob.job_open_date.label("employment_date"),
            StudentJob.company_name,
            StudentJob.salary,
        )
        return self._filter_job_student_ids(query, allowed_student_ids).order_by(StudentJob.salary.desc()).limit(limit).all()

    def get_student_employment_duration(self, db: Session, class_name: Optional[str] = None, allowed_student_ids: Optional[list[str]] = None):
        query = db.query(
            StudentJob.student_id,
            StudentJob.name,
            StudentJob.class_name,
            StudentJob.job_open_date,
            StudentJob.offer_date,
            func.datediff(StudentJob.offer_date, StudentJob.job_open_date).label("duration_days"),
        )
        query = self._filter_job_student_ids(query, allowed_student_ids)
        class_name = self._clean_optional_text(class_name)
        if class_name:
            query = query.filter(StudentJob.class_name == class_name)
        return query.all()

    def get_class_average_employment_duration(self, db: Session, class_name: Optional[str] = None, allowed_student_ids: Optional[list[str]] = None):
        duration = func.datediff(StudentJob.offer_date, StudentJob.job_open_date)
        query = db.query(StudentJob.class_name, func.avg(duration).label("average_duration_days"))
        query = self._filter_job_student_ids(query, allowed_student_ids)
        class_name = self._clean_optional_text(class_name)
        if class_name:
            query = query.filter(StudentJob.class_name == class_name)
        return query.group_by(StudentJob.class_name).all()

    def get_dashboard_summary(self, db: Session, allowed_student_ids: Optional[list[str]] = None):
        student_query = db.query(Student).filter(Student.is_deleted == False)
        student_query = self._filter_student_ids(student_query, allowed_student_ids)

        score_query = db.query(StudentScore).join(Student, StudentScore.student_id == Student.student_id).filter(Student.is_deleted == False)
        score_query = self._filter_student_ids(score_query, allowed_student_ids)

        job_query = db.query(StudentJob)
        job_query = self._filter_job_student_ids(job_query, allowed_student_ids)

        class_query = db.query(Class).filter(Class.is_deleted == False)
        if allowed_student_ids is not None:
            class_ids = [row[0] for row in student_query.with_entities(Student.class_id).distinct().all()]
            class_query = class_query.filter(Class.id.in_(class_ids)) if class_ids else class_query.filter(False)

        class_distribution = (
            student_query.with_entities(Class.class_id.label("class_id"), func.count(Student.id).label("student_count"))
            .join(Class, Student.class_id == Class.id)
            .group_by(Class.class_id)
            .order_by(func.count(Student.id).desc())
            .limit(8)
            .all()
        )
        employment_distribution = (
            job_query.with_entities(StudentJob.company_name, func.count(StudentJob.id).label("job_count"))
            .filter(StudentJob.company_name.isnot(None), StudentJob.company_name != "")
            .group_by(StudentJob.company_name)
            .order_by(func.count(StudentJob.id).desc())
            .limit(8)
            .all()
        )
        score_trends = (
            score_query.with_entities(StudentScore.exam_round, func.avg(StudentScore.score).label("average_score"))
            .filter(StudentScore.score.isnot(None))
            .group_by(StudentScore.exam_round)
            .order_by(StudentScore.exam_round.asc())
            .limit(12)
            .all()
        )
        recent_students = (
            student_query.with_entities(Student.student_id, Student.name, Student.class_id, Student.major, Student.enrollment_date)
            .order_by(Student.id.desc())
            .limit(8)
            .all()
        )

        return {
            "totals": {
                "students": student_query.count(),
                "teachers": db.query(Teacher).filter(Teacher.is_deleted == False).count(),
                "classes": class_query.count(),
                "scores": score_query.count(),
                "employment": job_query.count(),
            },
            "score_overview": {
                "average_score": round(float(score_query.with_entities(func.avg(StudentScore.score)).scalar() or 0), 2),
                "low_score_count": score_query.filter(StudentScore.score < 60).count(),
                "excellent_score_count": score_query.filter(StudentScore.score >= 90).count(),
            },
            "employment_overview": {
                "average_salary": round(float(job_query.with_entities(func.avg(StudentJob.salary)).scalar() or 0), 2),
                "top_salary": round(float(job_query.with_entities(func.max(StudentJob.salary)).scalar() or 0), 2),
            },
            "class_distribution": [
                {"class_id": item.class_id, "student_count": int(item.student_count or 0)} for item in class_distribution
            ],
            "employment_distribution": [
                {"company_name": item.company_name, "job_count": int(item.job_count or 0)} for item in employment_distribution
            ],
            "score_trends": [
                {"exam_round": item.exam_round, "average_score": round(float(item.average_score or 0), 2)} for item in score_trends
            ],
            "recent_students": [
                {
                    "student_id": item.student_id,
                    "name": item.name,
                    "class_id": item.class_id,
                    "major": item.major,
                    "enrollment_date": item.enrollment_date,
                }
                for item in recent_students
            ],
        }


statistics_dao = StatisticsDao()
