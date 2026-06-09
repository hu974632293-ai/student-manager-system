from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.controllers import dify_gateway as dify_gateway_api
from app.core.response import fail
from app.models.classes import Class
from app.models.student import Student
from app.models.user import User


def make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    User.__table__.create(engine)
    Class.__table__.create(engine)
    Student.__table__.create(engine)
    db = TestingSession()
    db.add(User(username="dify_admin", password_hash="hash", real_name="Dify Admin", role="admin", is_active=True))
    db.add(Class(id=1, class_id="AI01", is_deleted=False))
    db.add(Student(student_id="S001", class_id=1, name="张三", major="人工智能", is_deleted=False))
    db.commit()
    return db


def make_client(db):
    app = FastAPI()

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(status_code=exc.status_code, content=fail(str(exc.detail)))

    app.include_router(dify_gateway_api.dify_gateway_router)
    app.dependency_overrides[dify_gateway_api.get_db] = lambda: db
    return TestClient(app)


def test_dify_gateway_rejects_missing_token(monkeypatch):
    db = make_db()
    monkeypatch.setenv("DIFY_GATEWAY_API_KEY", "test-secret")
    monkeypatch.setenv("DIFY_GATEWAY_USERNAME", "dify_admin")

    response = make_client(db).post("/dify-gateway/students/query", json={"student_name": "张三"})

    assert response.status_code == 401
    assert response.json()["code"] == 0


def test_dify_gateway_queries_students_with_dedicated_token(monkeypatch):
    db = make_db()
    monkeypatch.setenv("DIFY_GATEWAY_API_KEY", "test-secret")
    monkeypatch.setenv("DIFY_GATEWAY_USERNAME", "dify_admin")

    response = make_client(db).post(
        "/dify-gateway/students/query",
        headers={"X-Dify-Token": "test-secret"},
        json={"query": "查询张三的学生信息", "student_name": "张三"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 1
    assert body["data"]["total"] == 1
    assert body["data"]["students"][0]["student_id"] == "S001"
    assert body["data"]["students"][0]["name"] == "张三"


def test_dify_gateway_reuses_rbac_permissions(monkeypatch):
    db = make_db()
    user = db.query(User).filter(User.username == "dify_admin").one()
    user.role = "student"
    db.commit()
    monkeypatch.setenv("DIFY_GATEWAY_API_KEY", "test-secret")
    monkeypatch.setenv("DIFY_GATEWAY_USERNAME", "dify_admin")

    response = make_client(db).post(
        "/dify-gateway/students/query",
        headers={"Authorization": "Bearer test-secret"},
        json={"student_name": "张三"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == 0
