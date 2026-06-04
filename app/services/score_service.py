from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.dao.score import ScoreDAO
from app.services.access_scope_service import AccessScopeService
from app.views.schemas.score import ScoreCreate, ScoreUpdate


class ScoreService:
    @staticmethod
    def _allowed_student_ids(db: Session, current_user=None):
        if current_user is None or AccessScopeService.is_admin(current_user):
            return None
        return AccessScopeService.allowed_student_ids(db, current_user)

    @staticmethod
    def create(db: Session, data: ScoreCreate, current_user=None):
        if current_user is not None and not AccessScopeService.can_access_student(db, current_user, data.student_id):
            return fail("permission denied")
        created_score = ScoreDAO.create_score(db, data.model_dump())
        if not created_score:
            return fail("score already exists")
        return success(ScoreDAO.with_student_name(db, created_score), "score created")

    @staticmethod
    def bulk_create(db: Session, scores: list[ScoreCreate], current_user=None):
        created_count = 0
        for score in scores:
            if current_user is not None and not AccessScopeService.can_access_student(db, current_user, score.student_id):
                return fail("permission denied", {"created_count": created_count})
            created = ScoreDAO.create_score(db, score.model_dump())
            if not created:
                return fail("some score records already exist", {"created_count": created_count})
            created_count += 1
        return success({"created_count": created_count, "total_requested": len(scores)}, "scores created")

    @staticmethod
    def get_one(db: Session, student_id: str, exam_round: int, current_user=None):
        if current_user is not None and not AccessScopeService.can_access_student(db, current_user, student_id):
            return fail("permission denied")
        score = ScoreDAO.get_score_by_student_and_round(db, student_id, exam_round)
        if not score:
            return fail("score not found")
        return success(ScoreDAO.with_student_name(db, score), "score found")

    @staticmethod
    def update(db: Session, student_id: str, exam_round: int, data: ScoreUpdate, current_user=None):
        if current_user is not None and not AccessScopeService.can_access_student(db, current_user, student_id):
            return fail("permission denied")
        score = ScoreDAO.get_score_by_student_and_round(db, student_id, exam_round)
        if not score:
            return fail("score not found")
        old_data = ScoreDAO.to_dict(score)
        updated = ScoreDAO.update_score(db, score, data.model_dump(exclude_unset=True))
        if not updated:
            return fail("no update fields")
        return success({"old_data": old_data, "new_data": ScoreDAO.with_student_name(db, updated)}, "score updated")

    @staticmethod
    def delete(db: Session, student_id: str, exam_round: int, current_user=None):
        if current_user is not None and not AccessScopeService.can_access_student(db, current_user, student_id):
            return fail("permission denied")
        score = ScoreDAO.get_score_by_student_and_round(db, student_id, exam_round)
        if not score:
            return fail("score not found")
        old_data = ScoreDAO.to_dict(score)
        ScoreDAO.delete_score(db, score)
        return success(old_data, "score deleted")

    @staticmethod
    def query_combined(db: Session, query, current_user=None):
        skip = (query.page - 1) * query.page_size
        scores, total = ScoreDAO.get_scores_combined(
            db,
            student_id=query.student_id,
            exam_round=query.exam_round,
            skip=skip,
            limit=query.page_size,
            allowed_student_ids=ScoreService._allowed_student_ids(db, current_user),
        )
        return success({"total": total, "items": scores}, "scores found")

    @staticmethod
    def query_by_range(db: Session, query, current_user=None):
        skip = (query.page - 1) * query.page_size
        scores, total = ScoreDAO.get_scores_by_range(
            db,
            min_score=query.min_score,
            max_score=query.max_score,
            skip=skip,
            limit=query.page_size,
            allowed_student_ids=ScoreService._allowed_student_ids(db, current_user),
        )
        return success({"total": total, "items": scores}, "scores found")
