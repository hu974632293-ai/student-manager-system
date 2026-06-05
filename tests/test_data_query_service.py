from types import SimpleNamespace

import pytest

from app.services import data_query_service
from app.services.data_query_service import DataQueryService
from app.views.schemas.data_query import DataQueryRequest


def test_prepare_sql_only_allows_select():
    with pytest.raises(ValueError):
        DataQueryService._prepare_sql("DELETE FROM students", 100)


def test_prepare_sql_rejects_unknown_table():
    with pytest.raises(ValueError):
        DataQueryService._prepare_sql("SELECT * FROM users", 100)


def test_prepare_sql_rewrites_limit():
    sql = DataQueryService._prepare_sql("SELECT students.name FROM students LIMIT 999", 20)
    assert sql == "SELECT students.name FROM students LIMIT 20"


def test_apply_teacher_scope_to_student_tables():
    sql = "SELECT students.name FROM students WHERE students.is_deleted = 0 LIMIT 10"
    scoped = DataQueryService._apply_access_scope(sql, ["S001"])
    assert "students.student_id IN :allowed_student_ids" in scoped
    assert scoped.endswith("LIMIT 10")


def test_nl2sql_returns_unified_success(monkeypatch):
    class FakeClient:
        def __init__(self):
            self.calls = 0

        def chat(self, messages):
            self.calls += 1
            if self.calls == 1:
                return '{"sql":"SELECT students.student_id, students.name FROM students WHERE students.is_deleted = 0"}'
            return "查询到 1 名学生。"

    class FakeDao:
        def execute_select(self, db, sql, allowed_student_ids=None):
            return ["student_id", "name"], [{"student_id": "S001", "name": "张三"}]

    monkeypatch.setattr(DataQueryService, "client", FakeClient())
    monkeypatch.setattr(data_query_service, "data_query_dao", FakeDao())

    user = SimpleNamespace(id=1, role="admin")
    payload = DataQueryRequest(question="查询学生", limit=10, show_sql=True)
    response = DataQueryService.nl2sql(SimpleNamespace(), payload, user)

    assert response["code"] == 1
    assert response["msg"] == "data query completed"
    assert response["data"]["row_count"] == 1
    assert response["data"]["summary"] == "查询到 1 名学生。"
