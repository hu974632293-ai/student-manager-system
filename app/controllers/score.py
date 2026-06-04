from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.controllers.auth import require_roles
from app.services.score_service import ScoreService
from app.views.schemas.score import ScoreCreate, ScoreQueryByRange, ScoreQueryCombined, ScoreUpdate


router_score = APIRouter(prefix="/score", tags=["score"])


@router_score.post("/", status_code=status.HTTP_201_CREATED, summary="新增学生成绩")
def create_score(
    score: ScoreCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return ScoreService.create(db, score, current_user=current_user)


@router_score.post("/bulk/", status_code=status.HTTP_201_CREATED, summary="批量新增学生成绩")
def bulk_create_scores(
    scores: List[ScoreCreate],
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return ScoreService.bulk_create(db, scores, current_user=current_user)


@router_score.put("/update/{student_id}/{exam_round}", summary="更新指定学生指定考试轮次成绩")
def update_score(
    student_id: str,
    exam_round: int,
    score_update: ScoreUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return ScoreService.update(db, student_id, exam_round, score_update, current_user=current_user)


@router_score.delete("/delete/{student_id}/{exam_round}", summary="删除指定学生指定考试轮次成绩")
def delete_score(
    student_id: str,
    exam_round: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return ScoreService.delete(db, student_id, exam_round, current_user=current_user)


@router_score.get("/query/", summary="按组合条件查询学生成绩")
def query_scores_combined(
    query: ScoreQueryCombined = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher", "student")),
):
    return ScoreService.query_combined(db, query, current_user=current_user)


@router_score.get("/range/", summary="按分数范围查询学生成绩")
def get_scores_by_range(
    query: ScoreQueryByRange = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher", "student")),
):
    return ScoreService.query_by_range(db, query, current_user=current_user)
