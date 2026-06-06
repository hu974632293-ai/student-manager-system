from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.controllers import auth as auth_api
from app.controllers import statistics as statistics_api
from app.core.database import Base
from app.dao.statistics import statistics_dao
from app.models.classes import Class
from app.models.student import Student
from app.services import statistics_service


def make_client():
    app = FastAPI()
    app.include_router(statistics_api.statistics_router)
    app.dependency_overrides[statistics_api.get_db] = lambda: object()
    app.dependency_overrides[auth_api.get_current_user] = lambda: type(
        "FakeUser",
        (),
        {"id": 1, "role": "admin", "teacher_id": None, "student_id": None},
    )()
    return TestClient(app)


def test_students_over_30_accepts_min_age_query(monkeypatch):
    captured = {}

    def fake_get_students_over_30(db, min_age, allowed_student_ids=None):
        captured["min_age"] = min_age
        captured["allowed_student_ids"] = allowed_student_ids
        return []

    monkeypatch.setattr(
        statistics_service.statistics_dao,
        "get_students_over_30",
        fake_get_students_over_30,
    )

    response = make_client().get("/statistics/students/over-30?min_age=25")

    assert response.status_code == 200
    assert response.json() == {"code": 1, "msg": "统计数据获取成功", "data": []}
    assert captured == {"min_age": 25, "allowed_student_ids": None}


def test_top_salary_students_keeps_default_limit(monkeypatch):
    captured = {}

    def fake_get_top5_salary_students(db, limit, allowed_student_ids=None):
        captured["limit"] = limit
        captured["allowed_student_ids"] = allowed_student_ids
        return []

    monkeypatch.setattr(
        statistics_service.statistics_dao,
        "get_top5_salary_students",
        fake_get_top5_salary_students,
    )

    response = make_client().get("/statistics/employment/top5-salary")

    assert response.status_code == 200
    assert response.json() == {"code": 1, "msg": "统计数据获取成功", "data": []}
    assert captured == {"limit": 5, "allowed_student_ids": None}


def test_failed_more_than_twice_accepts_score_and_count_queries(monkeypatch):
    captured = {}

    def fake_get_students_failed_more_than_twice(db, fail_score, min_fail_count, allowed_student_ids=None):
        captured["fail_score"] = fail_score
        captured["min_fail_count"] = min_fail_count
        captured["allowed_student_ids"] = allowed_student_ids
        return []

    monkeypatch.setattr(
        statistics_service.statistics_dao,
        "get_students_failed_more_than_twice",
        fake_get_students_failed_more_than_twice,
    )

    response = make_client().get(
        "/statistics/scores/failed-more-than-twice?fail_score=50&min_fail_count=1"
    )

    assert response.status_code == 200
    assert response.json() == {"code": 1, "msg": "统计数据获取成功", "data": []}
    assert captured == {"fail_score": 50.0, "min_fail_count": 1, "allowed_student_ids": None}


def test_invalid_limit_is_rejected():
    response = make_client().get("/statistics/employment/top5-salary?limit=0")

    assert response.status_code == 422


def test_class_gender_count_accepts_numeric_class_primary_id():
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = TestingSession()
    try:
        db.add(Class(id=2, class_id="PY0520", is_deleted=False))
        db.add_all(
            [
                Student(student_id="S001", class_id=2, name="A", gender="\u7537", is_deleted=False),
                Student(student_id="S002", class_id=2, name="B", gender="\u5973", is_deleted=False),
                Student(student_id="S003", class_id=2, name="C", gender="\u7537", is_deleted=False),
            ]
        )
        db.commit()

        result = statistics_dao.get_class_gender_counts(db, "2")

        assert len(result) == 1
        assert result[0].class_id == "PY0520"
        assert result[0].total_count == 3
        assert result[0].male_count == 2
        assert result[0].female_count == 1
    finally:
        db.close()


def test_class_gender_count_treats_blank_class_id_as_unfiltered():
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = TestingSession()
    try:
        db.add(Class(id=1, class_id="AI0409", is_deleted=False))
        db.add(Student(student_id="S001", class_id=1, name="A", gender="\u7537", is_deleted=False))
        db.commit()

        result = statistics_dao.get_class_gender_counts(db, " ")

        assert len(result) == 1
        assert result[0].class_id == "AI0409"
    finally:
        db.close()
