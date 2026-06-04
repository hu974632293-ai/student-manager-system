from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.controllers.auth import require_roles
from app.services.statistics_service import StatisticsService


statistics_router = APIRouter(prefix="/statistics", tags=["statistics"])


@statistics_router.get("/students/over-30", summary="统计年龄大于指定值的学生")
def get_students_over_30(
    min_age: int = Query(30, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return StatisticsService.get_students_over_30(db, min_age, current_user=current_user)


@statistics_router.get("/classes/gender-count", summary="统计班级学生性别人数")
def get_class_gender_counts(
    class_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return StatisticsService.get_class_gender_counts(db, class_id, current_user=current_user)


@statistics_router.get("/scores/all-above-80", summary="统计所有成绩高于指定分数的学生")
def get_students_all_scores_above_80(
    min_score: float = Query(80, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return StatisticsService.get_students_all_scores_above_80(db, min_score, current_user=current_user)


@statistics_router.get("/scores/failed-more-than-twice", summary="统计挂科次数超过指定次数的学生")
def get_students_failed_more_than_twice(
    fail_score: float = Query(60, ge=0, le=100),
    min_fail_count: int = Query(2, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return StatisticsService.get_students_failed_more_than_twice(db, fail_score, min_fail_count, current_user=current_user)


@statistics_router.get("/scores/class-average", summary="统计班级考试平均分")
def get_exam_class_average_scores(
    class_id: Optional[str] = Query(None),
    exam_round: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return StatisticsService.get_exam_class_average_scores(db, class_id, exam_round, current_user=current_user)


@statistics_router.get("/employment/top5-salary", summary="统计薪资排名靠前的学生就业信息")
def get_top5_salary_students(
    limit: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return StatisticsService.get_top_salary_students(db, limit, current_user=current_user)


@statistics_router.get("/employment/student-duration", summary="统计学生就业时长")
def get_student_employment_duration(
    class_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return StatisticsService.get_student_employment_duration(db, class_name, current_user=current_user)


@statistics_router.get("/employment/class-average-duration", summary="统计班级平均就业时长")
def get_class_average_employment_duration(
    class_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher")),
):
    return StatisticsService.get_class_average_employment_duration(db, class_name, current_user=current_user)
