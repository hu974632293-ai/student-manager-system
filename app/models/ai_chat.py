from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import relationship

from app.core.database import Base

# 跨数据库兼容的 JSON 类型
JSON = MySQLJSON


class AiChatSession(Base):
    __tablename__ = "ai_chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    summary = Column(Text, nullable=True)
    summary_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    messages = relationship("AiChatMessage", back_populates="session")


class AiChatMessage(Base):
    __tablename__ = "ai_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("ai_chat_sessions.session_id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    is_summarized = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    session = relationship("AiChatSession", back_populates="messages")

    __table_args__ = (
        Index("ix_ai_chat_messages_session_created", "session_id", "created_at"),
    )


class AiChatMemory(Base):
    __tablename__ = "ai_chat_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(20), nullable=False, default="manual")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_ai_chat_memories_user_active_created", "user_id", "is_active", "created_at"),
    )


class AiChatMessageVector(Base):
    """消息向量索引表 — 分离存储避免拖慢消息表普通查询。"""

    __tablename__ = "ai_chat_message_vectors"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("ai_chat_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    content_text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)
    model = Column(String(100), nullable=False, default="text-embedding-v3")
    created_at = Column(DateTime, server_default=func.now())
