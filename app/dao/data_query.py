from __future__ import annotations

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session


class DataQueryDao:
    def execute_select(
        self,
        db: Session,
        sql: str,
        allowed_student_ids: list[str] | None = None,
    ) -> tuple[list[str], list[dict]]:
        statement = text(sql)
        params = {}
        if allowed_student_ids is not None:
            statement = statement.bindparams(bindparam("allowed_student_ids", expanding=True))
            params["allowed_student_ids"] = allowed_student_ids
        result = db.execute(statement, params)
        rows = [self._normalize_row(dict(row)) for row in result.mappings().all()]
        return list(result.keys()), rows

    def _normalize_row(self, row: dict) -> dict:
        normalized = {}
        for key, value in row.items():
            if hasattr(value, "isoformat"):
                normalized[key] = value.isoformat()
            else:
                normalized[key] = value
        return normalized


data_query_dao = DataQueryDao()
