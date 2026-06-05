from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.logger import logger
from app.core.database import Base, engine


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
    """给 ai_chat 相关表补充长期记忆功能所需的新列和新表。"""
    try:
        # 检查 ai_chat_sessions 表是否存在
        inspector = inspect(engine)
        if "ai_chat_sessions" not in inspector.get_table_names():
            return  # 表尚未创建，由 create_all 统一处理

        # 新增列 — 只添加不存在的列
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
            existing_cols = {c["name"] for c in inspector.get_columns(table)}
            for col_name, col_def in columns:
                if col_name not in existing_cols:
                    statements.append(f"ALTER TABLE {table} ADD COLUMN {col_def}")

        # 新建 AiChatMessageVector 表（如果不存在）
        if "ai_chat_message_vectors" not in inspector.get_table_names():
            Base.metadata.tables["ai_chat_message_vectors"].create(bind=engine)
            logger.info("Created table: ai_chat_message_vectors")

        if not statements:
            return

        with engine.begin() as connection:
            for statement in statements:
                logger.info("Running: %s", statement)
                connection.execute(text(statement))
    except SQLAlchemyError:
        logger.warning("Schema migration for ai_chat memory features skipped or failed (may already be applied)")
