from sqlalchemy import inspect, text

from app.core.database import engine


def ensure_user_identity_columns() -> None:
    existing = {column["name"] for column in inspect(engine).get_columns("users")}
    statements = []
    if "teacher_id" not in existing:
        statements.append("ALTER TABLE users ADD COLUMN teacher_id INTEGER NULL")
    if "student_id" not in existing:
        if engine.dialect.name == "mysql":
            statements.append("ALTER TABLE users ADD COLUMN student_id VARCHAR(20) NULL")
        else:
            statements.append("ALTER TABLE users ADD COLUMN student_id TEXT NULL")
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
