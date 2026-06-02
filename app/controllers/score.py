from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.score_service import ScoreService
from app.views.schemas.score import ScoreCreate, ScoreQueryByRange, ScoreQueryCombined, ScoreUpdate


router_score = APIRouter(prefix="/score", tags=["score"])


@router_score.post("/", status_code=status.HTTP_201_CREATED)
def create_score(score: ScoreCreate, db: Session = Depends(get_db)):
    return ScoreService.create(db, score)


@router_score.post("/bulk/", status_code=status.HTTP_201_CREATED)
def bulk_create_scores(scores: List[ScoreCreate], db: Session = Depends(get_db)):
    return ScoreService.bulk_create(db, scores)


@router_score.put("/update/{student_id}/{exam_round}")
def update_score(student_id: str, exam_round: int, score_update: ScoreUpdate, db: Session = Depends(get_db)):
    return ScoreService.update(db, student_id, exam_round, score_update)


@router_score.delete("/delete/{student_id}/{exam_round}")
def delete_score(student_id: str, exam_round: int, db: Session = Depends(get_db)):
    return ScoreService.delete(db, student_id, exam_round)


@router_score.get("/query/")
def query_scores_combined(query: ScoreQueryCombined = Depends(), db: Session = Depends(get_db)):
    return ScoreService.query_combined(db, query)


@router_score.get("/range/")
def get_scores_by_range(query: ScoreQueryByRange = Depends(), db: Session = Depends(get_db)):
    return ScoreService.query_by_range(db, query)
