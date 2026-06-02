from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.classes import Class
from app.models.job import StudentJob
from app.models.score import StudentScore
from app.models.student import Student


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

    def get_students_over_30(self, db: Session, min_age: int = 30):
        return db.query(Student).filter(Student.is_deleted == False, Student.age > min_age).all()

    def get_class_gender_counts(self, db: Session, class_id: Optional[str] = None):
        query = db.query(
            Class.class_id.label("class_id"),
            func.count(Student.id).label("total_count"),
            func.sum(case((Student.gender == "\u7537", 1), else_=0)).label("male_count"),
            func.sum(case((Student.gender == "\u5973", 1), else_=0)).label("female_count"),
        ).join(Student, Student.class_id == Class.id).filter(Class.is_deleted == False, Student.is_deleted == False)
        class_id = self._clean_optional_text(class_id)
        if class_id:
            if class_id.isdigit():
                query = query.filter((Class.id == int(class_id)) | (Class.class_id == class_id))
            else:
                query = query.filter(Class.class_id == class_id)
        return query.group_by(Class.class_id).all()

    def get_students_all_scores_above_80(self, db: Session, min_score: float = 80):
        subquery = db.query(StudentScore.student_id).group_by(StudentScore.student_id).having(func.min(StudentScore.score) >= min_score).subquery()
        return db.query(Student.student_id, Student.name, StudentScore.exam_round, StudentScore.score).join(
            StudentScore, Student.student_id == StudentScore.student_id
        ).filter(Student.student_id.in_(subquery)).all()

    def get_students_failed_more_than_twice(self, db: Session, fail_score: float = 60, min_fail_count: int = 2):
        failed = db.query(StudentScore.student_id).filter(StudentScore.score < fail_score).group_by(StudentScore.student_id).having(
            func.count(StudentScore.id) > min_fail_count
        ).subquery()
        return db.query(Student.name, Class.class_id, StudentScore.exam_round, StudentScore.score).join(
            StudentScore, Student.student_id == StudentScore.student_id
        ).join(Class, Student.class_id == Class.id).filter(Student.student_id.in_(failed), StudentScore.score < fail_score).all()

    def get_exam_class_average_scores(self, db: Session, class_id: Optional[str] = None, exam_round: Optional[int] = None):
        query = db.query(
            StudentScore.exam_round,
            Class.class_id.label("class_id"),
            func.avg(StudentScore.score).label("average_score"),
        ).join(Student, StudentScore.student_id == Student.student_id).join(Class, Student.class_id == Class.id)
        class_id = self._clean_optional_text(class_id)
        if class_id:
            if class_id.isdigit():
                query = query.filter((Class.id == int(class_id)) | (Class.class_id == class_id))
            else:
                query = query.filter(Class.class_id == class_id)
        if exam_round is not None:
            query = query.filter(StudentScore.exam_round == exam_round)
        return query.group_by(StudentScore.exam_round, Class.class_id).all()

    def get_top5_salary_students(self, db: Session, limit: int = 5):
        return db.query(
            StudentJob.name,
            StudentJob.class_name,
            StudentJob.job_open_date.label("employment_date"),
            StudentJob.company_name,
            StudentJob.salary,
        ).order_by(StudentJob.salary.desc()).limit(limit).all()

    def get_student_employment_duration(self, db: Session, class_name: Optional[str] = None):
        query = db.query(
            StudentJob.student_id,
            StudentJob.name,
            StudentJob.class_name,
            StudentJob.job_open_date,
            StudentJob.offer_date,
            (func.julianday(StudentJob.offer_date) - func.julianday(StudentJob.job_open_date)).label("duration_days"),
        )
        class_name = self._clean_optional_text(class_name)
        if class_name:
            query = query.filter(StudentJob.class_name == class_name)
        return query.all()

    def get_class_average_employment_duration(self, db: Session, class_name: Optional[str] = None):
        duration = func.julianday(StudentJob.offer_date) - func.julianday(StudentJob.job_open_date)
        query = db.query(StudentJob.class_name, func.avg(duration).label("average_duration_days"))
        class_name = self._clean_optional_text(class_name)
        if class_name:
            query = query.filter(StudentJob.class_name == class_name)
        return query.group_by(StudentJob.class_name).all()


statistics_dao = StatisticsDao()
