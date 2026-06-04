from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.score import StudentScore
from app.models.student import Student


class ScoreDAO:
    @staticmethod
    def to_dict(score: StudentScore) -> dict:
        return {
            "id": score.id,
            "student_id": score.student_id,
            "exam_round": score.exam_round,
            "score": score.score,
            "remark": score.remark,
        }

    @staticmethod
    def with_student_name(db: Session, score: StudentScore) -> dict:
        data = ScoreDAO.to_dict(score)
        student = db.query(Student).filter(Student.student_id == score.student_id).first()
        data["student_name"] = student.name if student else "unknown"
        return data

    @staticmethod
    def create_score(db: Session, score_data: dict):
        exists = ScoreDAO.get_score_by_student_and_round(
            db,
            score_data["student_id"],
            score_data["exam_round"],
        )
        if exists:
            return None
        db_score = StudentScore(**score_data)
        db.add(db_score)
        db.commit()
        db.refresh(db_score)
        return db_score

    @staticmethod
    def delete_score(db: Session, score: StudentScore) -> None:
        db.delete(score)
        db.commit()

    @staticmethod
    def update_score(db: Session, score: StudentScore, score_data: dict):
        if not score_data:
            return None
        for key, value in score_data.items():
            setattr(score, key, value)
        db.commit()
        db.refresh(score)
        return score

    @staticmethod
    def get_score_by_student_and_round(db: Session, student_id: str, exam_round: int):
        return db.query(StudentScore).filter(
            and_(
                StudentScore.student_id == student_id,
                StudentScore.exam_round == exam_round,
            )
        ).first()

    @staticmethod
    def get_scores_combined(
        db: Session,
        student_id: Optional[str] = None,
        exam_round: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        allowed_student_ids: Optional[list[str]] = None,
    ):
        query = db.query(StudentScore, Student.name.label("student_name")).join(
            Student,
            StudentScore.student_id == Student.student_id,
        )
        count_query = db.query(func.count(StudentScore.id))
        if allowed_student_ids is not None:
            if not allowed_student_ids:
                return [], 0
            query = query.filter(StudentScore.student_id.in_(allowed_student_ids))
            count_query = count_query.filter(StudentScore.student_id.in_(allowed_student_ids))
        if student_id is not None:
            query = query.filter(StudentScore.student_id == student_id)
            count_query = count_query.filter(StudentScore.student_id == student_id)
        if exam_round is not None:
            query = query.filter(StudentScore.exam_round == exam_round)
            count_query = count_query.filter(StudentScore.exam_round == exam_round)
        items = []
        for score_obj, student_name in query.offset(skip).limit(limit).all():
            data = ScoreDAO.to_dict(score_obj)
            data["student_name"] = student_name
            items.append(data)
        return items, count_query.scalar()

    @staticmethod
    def get_scores_by_range(
        db: Session,
        min_score: float = 0,
        max_score: float = 100,
        skip: int = 0,
        limit: int = 100,
        allowed_student_ids: Optional[list[str]] = None,
    ):
        query = db.query(StudentScore, Student.name.label("student_name")).join(
            Student,
            StudentScore.student_id == Student.student_id,
        ).filter(
            StudentScore.score.isnot(None),
            StudentScore.score >= min_score,
            StudentScore.score <= max_score,
        )
        count_query = db.query(func.count(StudentScore.id)).filter(
            StudentScore.score.isnot(None),
            StudentScore.score >= min_score,
            StudentScore.score <= max_score,
        )
        if allowed_student_ids is not None:
            if not allowed_student_ids:
                return [], 0
            query = query.filter(StudentScore.student_id.in_(allowed_student_ids))
            count_query = count_query.filter(StudentScore.student_id.in_(allowed_student_ids))
        total = count_query.scalar()
        items = []
        for score_obj, student_name in query.offset(skip).limit(limit).all():
            data = ScoreDAO.to_dict(score_obj)
            data["student_name"] = student_name
            items.append(data)
        return items, total
