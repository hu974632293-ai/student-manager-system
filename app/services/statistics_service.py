from sqlalchemy.orm import Session

from app.core.response import success
from app.dao.statistics import statistics_dao
from app.services.access_scope_service import AccessScopeService


class StatisticsService:
    @staticmethod
    def _plain(data):
        if isinstance(data, list):
            return [StatisticsService._plain(item) for item in data]
        if hasattr(data, "_mapping"):
            return dict(data._mapping)
        return data

    @staticmethod
    def _allowed_student_ids(db: Session, current_user=None):
        if current_user is None or AccessScopeService.is_admin(current_user):
            return None
        return AccessScopeService.allowed_student_ids(db, current_user)

    @staticmethod
    def get_students_over_30(db: Session, min_age: int = 30, current_user=None):
        return success(StatisticsService._plain(statistics_dao.get_students_over_30(db, min_age, StatisticsService._allowed_student_ids(db, current_user))), "statistics found")

    @staticmethod
    def get_class_gender_counts(db: Session, class_id=None, current_user=None):
        return success(StatisticsService._plain(statistics_dao.get_class_gender_counts(db, class_id, StatisticsService._allowed_student_ids(db, current_user))), "statistics found")

    @staticmethod
    def get_students_all_scores_above_80(db: Session, min_score: float = 80, current_user=None):
        return success(StatisticsService._plain(statistics_dao.get_students_all_scores_above_80(db, min_score, StatisticsService._allowed_student_ids(db, current_user))), "statistics found")

    @staticmethod
    def get_students_failed_more_than_twice(db: Session, fail_score: float = 60, min_fail_count: int = 2, current_user=None):
        return success(
            StatisticsService._plain(statistics_dao.get_students_failed_more_than_twice(db, fail_score, min_fail_count, StatisticsService._allowed_student_ids(db, current_user))),
            "statistics found",
        )

    @staticmethod
    def get_exam_class_average_scores(db: Session, class_id=None, exam_round=None, current_user=None):
        return success(StatisticsService._plain(statistics_dao.get_exam_class_average_scores(db, class_id, exam_round, StatisticsService._allowed_student_ids(db, current_user))), "statistics found")

    @staticmethod
    def get_top_salary_students(db: Session, limit: int = 5, current_user=None):
        return success(StatisticsService._plain(statistics_dao.get_top5_salary_students(db, limit, StatisticsService._allowed_student_ids(db, current_user))), "statistics found")

    @staticmethod
    def get_student_employment_duration(db: Session, class_name=None, current_user=None):
        return success(StatisticsService._plain(statistics_dao.get_student_employment_duration(db, class_name, StatisticsService._allowed_student_ids(db, current_user))), "statistics found")

    @staticmethod
    def get_class_average_employment_duration(db: Session, class_name=None, current_user=None):
        return success(StatisticsService._plain(statistics_dao.get_class_average_employment_duration(db, class_name, StatisticsService._allowed_student_ids(db, current_user))), "statistics found")

    @staticmethod
    def get_dashboard_summary(db: Session, current_user=None):
        return success(
            statistics_dao.get_dashboard_summary(db, StatisticsService._allowed_student_ids(db, current_user)),
            "dashboard statistics found",
        )
