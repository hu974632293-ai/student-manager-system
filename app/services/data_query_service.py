from __future__ import annotations

import json
import logging
import re

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.permissions import ROLE_ADMIN, ROLE_TEACHER
from app.core.qwen_client import QwenClient, QwenRequestError, QwenResponseError
from app.core.qwen_config import QwenConfigError
from app.core.response import fail, success
from app.dao.data_query import data_query_dao
from app.services.access_scope_service import AccessScopeService
from app.views.schemas.data_query import DataQueryRequest

logger = logging.getLogger(__name__)


class DataQueryService:
    allowed_tables = {
        "students",
        "classes",
        "teachers",
        "student_scores",
        "student_jobs",
        "class_teacher_link",
    }
    soft_delete_tables = {"students", "classes", "teachers", "student_jobs"}
    sql_keywords = {
        "where",
        "join",
        "inner",
        "left",
        "right",
        "full",
        "cross",
        "on",
        "group",
        "order",
        "having",
        "limit",
    }
    forbidden_words = {
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "replace",
        "grant",
        "revoke",
        "call",
        "load",
        "outfile",
        "infile",
        "into",
        "users",
        "mysql",
        "information_schema",
        "performance_schema",
        "sys",
    }
    table_descriptions = """
可查询表和字段如下，禁止使用未列出的表：
1. students：学生表。字段：id、student_id、class_id、name、native_place、graduate_school、major、enrollment_date、graduation_date、education、consultant_id、age、gender、is_deleted。
2. classes：班级表。字段：id、class_id、start_date、head_teacher、description、is_deleted。
3. teachers：教师表。字段：id、teacher_number、name、gender、phone、email、subject、is_active、is_deleted。
4. student_scores：学生成绩表。字段：id、student_id、exam_round、score、remark。
5. student_jobs：学生就业表。字段：id、student_id、name、class_name、job_open_date、offer_date、company_name、salary、position、is_deleted。
6. class_teacher_link：班级教师关系表。字段：class_id、teacher_id。
关系说明：
- students.class_id = classes.id。
- student_scores.student_id = students.student_id。
- student_jobs.student_id = students.student_id。
- students.consultant_id = teachers.id。
- class_teacher_link.class_id = classes.id，class_teacher_link.teacher_id = teachers.id。
"""
    client: QwenClient | None = None

    @classmethod
    def get_client(cls) -> QwenClient:
        if cls.client is None:
            cls.client = QwenClient()
        return cls.client

    @classmethod
    def nl2sql(cls, db: Session, payload: DataQueryRequest, current_user):
        question = payload.question.strip()
        if not question:
            return fail("question is required")
        if current_user.role not in (ROLE_ADMIN, ROLE_TEACHER):
            return fail("permission denied")

        safe_limit = min(max(int(payload.limit), 1), 100)
        allowed_student_ids = (
            None
            if AccessScopeService.is_admin(current_user)
            else AccessScopeService.allowed_student_ids(db, current_user)
        )
        if allowed_student_ids == []:
            return success(
                {
                    "question": question,
                    "sql": "",
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "summary": "当前账号没有可查询的学生数据范围。",
                },
                "data query completed",
            )

        try:
            raw_sql = cls._generate_sql(question, safe_limit, current_user.role)
            sql = cls._prepare_sql(raw_sql, safe_limit)
            sql = cls._apply_access_scope(sql, allowed_student_ids)
            columns, rows = data_query_dao.execute_select(db, sql, allowed_student_ids)
            summary = cls._beautify_result(question, sql, columns, rows)
            logger.info(
                "NL2SQL query user_id=%s role=%s rows=%s sql=%s",
                getattr(current_user, "id", None),
                current_user.role,
                len(rows),
                sql,
            )
            return success(
                {
                    "question": question,
                    "sql": sql if payload.show_sql else "",
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "summary": summary,
                },
                "data query completed",
            )
        except SQLAlchemyError:
            db.rollback()
            logger.exception("NL2SQL query failed")
            return fail("智能问数查询执行失败，请调整问题或稍后重试")
        except (QwenConfigError, QwenRequestError, QwenResponseError) as exc:
            logger.exception("NL2SQL model request failed")
            return fail(str(exc))
        except ValueError as exc:
            logger.warning("NL2SQL rejected: %s", exc)
            return fail(str(exc))

    @classmethod
    def _generate_sql(cls, question: str, limit: int, role: str) -> str:
        prompt = f"""
你是学生管理系统的 NL2SQL 助手。请根据用户问题生成 MySQL SELECT 查询。

规则：
- 只返回 JSON，不要解释，格式必须是 {{"sql":"SELECT ..."}}。
- 只能使用 SELECT，禁止写入、删除、更新、建表、删表和多语句。
- 只能使用白名单表，不能查询 users 或任何系统表。
- 不要使用表别名，所有字段都用 表名.字段名。
- 软删除数据需要过滤 is_deleted = 0；教师启用状态需要过滤 is_active = 1。
- 结果最多 LIMIT {limit}。
- 当前用户角色是 {role}。

{cls.table_descriptions}

用户问题：{question}
"""
        content = cls.get_client().chat([{"role": "user", "content": prompt}])
        data = cls._load_json_object(content)
        sql = str(data.get("sql") or "").strip()
        if not sql:
            raise ValueError("模型未生成 SQL")
        return sql

    @classmethod
    def _load_json_object(cls, content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
            text = re.sub(r"```$", "", text).strip()
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            text = match.group(0)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("模型返回的 SQL JSON 格式无效") from exc
        if not isinstance(data, dict):
            raise ValueError("模型返回的 SQL JSON 必须是对象")
        return data

    @classmethod
    def _prepare_sql(cls, sql: str, limit: int) -> str:
        cleaned = sql.strip().strip(";").strip()
        cleaned = cls._remove_invalid_soft_delete_filters(cleaned)
        cls._validate_sql(cleaned)
        without_limit = cls._strip_trailing_limit(cleaned)
        return f"{without_limit} LIMIT {limit}"

    @classmethod
    def _remove_invalid_soft_delete_filters(cls, sql: str) -> str:
        for table in sorted(cls.allowed_tables - cls.soft_delete_tables):
            column = rf"`?{re.escape(table)}`?\.`?is_deleted`?"
            condition = rf"{column}\s*=\s*(?:0|false)"
            sql = re.sub(rf"\s+AND\s+{condition}", "", sql, flags=re.IGNORECASE)
            sql = re.sub(rf"{condition}\s+AND\s+", "", sql, flags=re.IGNORECASE)
            sql = re.sub(rf"\bWHERE\s+{condition}\s*$", "", sql, flags=re.IGNORECASE)
            sql = re.sub(
                rf"\bWHERE\s+{condition}\s+(GROUP\s+BY|HAVING|ORDER\s+BY|LIMIT)\b",
                r"\1",
                sql,
                flags=re.IGNORECASE,
            )
        return re.sub(r"\s+", " ", sql).strip()

    @classmethod
    def _validate_sql(cls, sql: str) -> None:
        normalized = re.sub(r"\s+", " ", sql.strip()).lower()
        if not normalized.startswith("select "):
            raise ValueError("智能问数只允许执行 SELECT 查询")
        if ";" in normalized or "--" in normalized or "/*" in normalized or "#" in normalized:
            raise ValueError("SQL 不能包含多语句或注释")
        tokens = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", normalized))
        forbidden = tokens & cls.forbidden_words
        if forbidden:
            raise ValueError(f"SQL 包含禁止访问的关键字或表：{', '.join(sorted(forbidden))}")
        tables = set(re.findall(r"\b(?:from|join)\s+`?([a-zA-Z_][a-zA-Z0-9_]*)`?", normalized))
        if not tables:
            raise ValueError("SQL 必须包含可查询业务表")
        unknown_tables = tables - cls.allowed_tables
        if unknown_tables:
            raise ValueError(f"SQL 访问了非白名单表：{', '.join(sorted(unknown_tables))}")
        for alias in re.findall(
            r"\b(?:from|join)\s+`?[a-zA-Z_][a-zA-Z0-9_]*`?\s+(?:as\s+)?([a-zA-Z_][a-zA-Z0-9_]*)",
            normalized,
        ):
            if alias not in cls.sql_keywords:
                raise ValueError("智能问数暂不支持 SQL 表别名")

    @staticmethod
    def _strip_trailing_limit(sql: str) -> str:
        return re.sub(
            r"\s+limit\s+\d+(?:\s*,\s*\d+|\s+offset\s+\d+)?\s*$",
            "",
            sql,
            flags=re.IGNORECASE,
        ).strip()

    @classmethod
    def _apply_access_scope(cls, sql: str, allowed_student_ids: list[str] | None) -> str:
        if allowed_student_ids is None:
            return sql
        normalized = sql.lower()
        conditions = []
        if "students" in normalized:
            conditions.append("students.student_id IN :allowed_student_ids")
        if "student_scores" in normalized:
            conditions.append("student_scores.student_id IN :allowed_student_ids")
        if "student_jobs" in normalized:
            conditions.append("student_jobs.student_id IN :allowed_student_ids")
        if not conditions:
            return sql
        condition = "(" + " AND ".join(sorted(set(conditions))) + ")"
        without_limit = cls._strip_trailing_limit(sql)
        limit_match = re.search(r"\s+limit\s+\d+\s*$", sql, flags=re.IGNORECASE)
        limit_clause = limit_match.group(0).strip() if limit_match else ""
        insert_match = re.search(
            r"\s+(group\s+by|order\s+by|having)\s+",
            without_limit,
            flags=re.IGNORECASE,
        )
        if insert_match:
            head = without_limit[: insert_match.start()]
            tail = without_limit[insert_match.start() :]
        else:
            head = without_limit
            tail = ""
        connector = " AND " if re.search(r"\bwhere\b", head, flags=re.IGNORECASE) else " WHERE "
        scoped = f"{head}{connector}{condition}{tail}"
        return f"{scoped} {limit_clause}".strip()

    @classmethod
    def _beautify_result(cls, question: str, sql: str, columns: list[str], rows: list[dict]) -> str:
        if not rows:
            return "没有查询到符合条件的数据。"
        preview_rows = rows[:20]
        prompt = f"""
请把智能问数 SQL 查询结果整理成简洁中文结论。
要求：
- 不要编造查询结果之外的数据。
- 优先说明关键数字、排名、平均值、总数等结论。
- 结论控制在 120 字以内。

用户问题：{question}
执行 SQL：{sql}
列名：{json.dumps(columns, ensure_ascii=False)}
结果数据：{json.dumps(preview_rows, ensure_ascii=False)}
"""
        try:
            return cls.get_client().chat([{"role": "user", "content": prompt}]).strip()
        except Exception as exc:
            logger.warning("NL2SQL summary beautify failed: %s", exc)
            return f"查询完成，共返回 {len(rows)} 条数据。"
