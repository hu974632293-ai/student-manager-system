from sqlalchemy.orm import Session

from app.core.response import success
from app.dao.statistics import statistics_dao


class StatisticsService:
    @staticmethod
    def get_students_over_30(db: Session, min_age: int = 30):
        return success(statistics_dao.get_students_over_30(db, min_age), "statistics found")

    @staticmethod
    def get_class_gender_counts(db: Session, class_id=None):
        return success(statistics_dao.get_class_gender_counts(db, class_id), "statistics found")

    @staticmethod
    def get_students_all_scores_above_80(db: Session, min_score: float = 80):
        return success(statistics_dao.get_students_all_scores_above_80(db, min_score), "statistics found")

    @staticmethod
    def get_students_failed_more_than_twice(db: Session, fail_score: float = 60, min_fail_count: int = 2):
        return success(
            statistics_dao.get_students_failed_more_than_twice(db, fail_score, min_fail_count),
            "statistics found",
        )

    @staticmethod
    def get_exam_class_average_scores(db: Session, class_id=None, exam_round=None):
        return success(statistics_dao.get_exam_class_average_scores(db, class_id, exam_round), "statistics found")

    @staticmethod
    def get_top_salary_students(db: Session, limit: int = 5):
        return success(statistics_dao.get_top5_salary_students(db, limit), "statistics found")

    @staticmethod
    def get_student_employment_duration(db: Session, class_name=None):
        return success(statistics_dao.get_student_employment_duration(db, class_name), "statistics found")

    @staticmethod
    def get_class_average_employment_duration(db: Session, class_name=None):
        return success(statistics_dao.get_class_average_employment_duration(db, class_name), "statistics found")
