from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import Base, engine
from app.core.logger import logger


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


def ensure_ai_chat_schema_compat() -> None:
    """为 ai_chat 相关表补齐长期记忆、摘要和向量检索所需结构。"""
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        if "ai_chat_sessions" not in existing_tables:
            return

        for table_name in ("ai_chat_memories", "ai_chat_message_vectors"):
            if table_name not in existing_tables:
                Base.metadata.tables[table_name].create(bind=engine)
                logger.info("Created table: %s", table_name)

        inspector = inspect(engine)
        columns_to_add = {
            "ai_chat_sessions": [
                ("user_id", "INTEGER NULL"),
                ("summary", "TEXT NULL"),
                ("summary_updated_at", "DATETIME NULL"),
            ],
            "ai_chat_messages": [
                ("token_count", "INTEGER NULL"),
                ("is_summarized", "TINYINT(1) NOT NULL DEFAULT 0"),
            ],
            "ai_chat_memories": [
                ("embedding", "JSON NULL"),
            ],
        }

        statements = []
        for table, columns in columns_to_add.items():
            existing_cols = {column["name"] for column in inspector.get_columns(table)}
            for col_name, col_def in columns:
                if col_name not in existing_cols:
                    statements.append(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")

        if not statements:
            return

        with engine.begin() as connection:
            for statement in statements:
                logger.info("Running: %s", statement)
                connection.execute(text(statement))
    except SQLAlchemyError:
        logger.exception("Schema migration for ai_chat memory features failed")
