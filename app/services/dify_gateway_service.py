from __future__ import annotations

import re
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.dao import students as student_dao
from app.models.student import Student
from app.services.access_scope_service import AccessScopeService
from app.views.schemas.dify_gateway import DifyStudentQueryRequest


class DifyGatewayService:
    @staticmethod
    def _clean_text(value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
        return value or None

    @staticmethod
    def _extract_filters(payload: DifyStudentQueryRequest) -> dict:
        filters = {
            "student_id": DifyGatewayService._clean_text(payload.student_id),
            "student_name": DifyGatewayService._clean_text(payload.student_name),
            "class_id": payload.class_id,
        }
        query = DifyGatewayService._clean_text(payload.query)
        if not query:
            return filters

        if not filters["student_id"]:
            student_id_match = re.search(r"(?:学号|student_id|编号)[:：\s]*([A-Za-z0-9_-]{2,20})", query, re.IGNORECASE)
            if student_id_match:
                filters["student_id"] = student_id_match.group(1)

        if filters["class_id"] is None:
            class_id_match = re.search(r"(?:班级|class_id)[:：\s]*(\d+)", query, re.IGNORECASE)
            if class_id_match:
                filters["class_id"] = int(class_id_match.group(1))

        if not filters["student_name"]:
            name_match = re.search(r"(?:姓名|学生|查询|查找|找一下)[:：\s]*([\u4e00-\u9fa5]{2,8})", query)
            if name_match:
                filters["student_name"] = name_match.group(1)

        return filters

    @staticmethod
    def _serialize_value(value):
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value

    @staticmethod
    def _serialize_student(student: Student) -> dict:
        fields = [
            "id",
            "student_id",
            "class_id",
            "name",
            "native_place",
            "graduate_school",
            "major",
            "enrollment_date",
            "graduation_date",
            "education",
            "consultant_id",
            "age",
            "gender",
        ]
        return {field: DifyGatewayService._serialize_value(getattr(student, field)) for field in fields}

    @staticmethod
    def query_students(db: Session, payload: DifyStudentQueryRequest, current_user):
        filters = DifyGatewayService._extract_filters(payload)
        students, total = student_dao.query_students(
            db,
            student_id=filters["student_id"],
            student_name=filters["student_name"],
            class_id=filters["class_id"],
            skip=payload.skip,
            limit=payload.limit,
            **StudentServiceScope.scope_kwargs(db, current_user),
        )
        if total == 0:
            return fail(
                "未查询到符合条件的学生",
                {
                    "query": payload.query,
                    "filters": filters,
                    "total": 0,
                    "students": [],
                },
            )
        return success(
            {
                "query": payload.query,
                "filters": filters,
                "total": total,
                "students": [DifyGatewayService._serialize_student(student) for student in students],
            },
            "Dify 学生查询成功",
        )


class StudentServiceScope:
    @staticmethod
    def scope_kwargs(db: Session, current_user) -> dict:
        if current_user is None or AccessScopeService.is_admin(current_user):
            return {}
        return {"student_ids": AccessScopeService.allowed_student_ids(db, current_user)}
