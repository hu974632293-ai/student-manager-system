import json

from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models.ai_chat import AiChatMemory, AiChatMessage, AiChatMessageVector, AiChatSession


class AiChatDao:
    def get_session(self, db: Session, session_id: str):
        return db.query(AiChatSession).filter(AiChatSession.session_id == session_id).first()

    def create_session(self, db: Session, session_id: str, title: str = None, user_id: int = None):
        session = AiChatSession(session_id=session_id, title=title, user_id=user_id)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def list_user_sessions(self, db: Session, user_id: int, keyword: str = None, limit: int = 50):
        query = db.query(AiChatSession).filter(AiChatSession.user_id == user_id)
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(or_(AiChatSession.title.like(like), AiChatSession.session_id.like(like)))
        return (
            query.order_by(AiChatSession.updated_at.desc(), AiChatSession.id.desc())
            .limit(limit)
            .all()
        )

    def update_session_title(self, db: Session, session_id: str, user_id: int, title: str):
        session = (
            db.query(AiChatSession)
            .filter(AiChatSession.session_id == session_id, AiChatSession.user_id == user_id)
            .first()
        )
        if not session:
            return None
        session.title = title
        session.updated_at = func.now()
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def delete_session(self, db: Session, session_id: str, user_id: int) -> bool:
        session = (
            db.query(AiChatSession)
            .filter(AiChatSession.session_id == session_id, AiChatSession.user_id == user_id)
            .first()
        )
        if not session:
            return False
        db.query(AiChatMessageVector).filter(AiChatMessageVector.session_id == session_id).delete()
        db.query(AiChatMessage).filter(AiChatMessage.session_id == session_id).delete()
        db.delete(session)
        db.commit()
        return True

    def touch_session(self, db: Session, session_id: str):
        session = self.get_session(db, session_id)
        if not session:
            return None
        session.updated_at = func.now()
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def create_message(self, db: Session, session_id: str, role: str, content: str):
        message = AiChatMessage(session_id=session_id, role=role, content=content)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def list_recent_messages(self, db: Session, session_id: str, limit: int):
        messages = (
            db.query(AiChatMessage)
            .filter(AiChatMessage.session_id == session_id)
            .order_by(AiChatMessage.created_at.desc(), AiChatMessage.id.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(messages))

    def create_memory(self, db: Session, user_id: int, content: str, source: str = "manual"):
        memory = AiChatMemory(user_id=user_id, content=content, source=source)
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    def list_memories(self, db: Session, user_id: int, limit: int = 20):
        memories = (
            db.query(AiChatMemory)
            .filter(AiChatMemory.user_id == user_id, AiChatMemory.is_active == True)
            .order_by(AiChatMemory.created_at.desc(), AiChatMemory.id.desc())
            .limit(limit)
            .all()
        )
        return memories

    def get_memory(self, db: Session, memory_id: int, user_id: int):
        return (
            db.query(AiChatMemory)
            .filter(AiChatMemory.id == memory_id, AiChatMemory.user_id == user_id, AiChatMemory.is_active == True)
            .first()
        )

    def deactivate_memory(self, db: Session, memory_id: int, user_id: int):
        memory = self.get_memory(db, memory_id, user_id)
        if not memory:
            return None
        memory.is_active = False
        memory.updated_at = func.now()
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    # ─── 会话摘要 ─────────────────────────────

    def get_session_summary(self, db: Session, session_id: str) -> str | None:
        session = self.get_session(db, session_id)
        return session.summary if session else None

    def update_session_summary(
        self, db: Session, session_id: str, summary_text: str
    ) -> AiChatSession | None:
        session = self.get_session(db, session_id)
        if not session:
            return None
        session.summary = summary_text
        session.summary_updated_at = func.now()
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def set_session_user(self, db: Session, session_id: str, user_id: int) -> AiChatSession | None:
        session = self.get_session(db, session_id)
        if not session:
            return None
        session.user_id = user_id
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def list_user_session_ids(self, db: Session, user_id: int, limit: int = 20) -> list[str]:
        sessions = (
            db.query(AiChatSession)
            .filter(AiChatSession.user_id == user_id)
            .order_by(AiChatSession.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [s.session_id for s in sessions]

    def list_all_session_messages(self, db: Session, session_id: str) -> list[AiChatMessage]:
        return (
            db.query(AiChatMessage)
            .filter(AiChatMessage.session_id == session_id)
            .order_by(AiChatMessage.created_at.asc(), AiChatMessage.id.asc())
            .all()
        )

    def mark_messages_summarized(self, db: Session, session_id: str, upto_message_id: int):
        db.query(AiChatMessage).filter(
            AiChatMessage.session_id == session_id,
            AiChatMessage.id <= upto_message_id,
        ).update({AiChatMessage.is_summarized: True})
        db.commit()

    # ─── 消息向量 ─────────────────────────────

    def create_message_vector(
        self,
        db: Session,
        message_id: int,
        session_id: str,
        content_text: str,
        embedding: list[float],
        model: str = "text-embedding-v3",
    ) -> AiChatMessageVector:
        vector = AiChatMessageVector(
            session_id=session_id,
            message_id=message_id,
            content_text=content_text,
            embedding=json.dumps(embedding),
            model=model,
        )
        db.add(vector)
        db.commit()
        db.refresh(vector)
        return vector

    def list_message_vectors_by_sessions(
        self,
        db: Session,
        session_ids: list[str],
        limit: int = 200,
    ) -> list[AiChatMessageVector]:
        return (
            db.query(AiChatMessageVector)
            .filter(AiChatMessageVector.session_id.in_(session_ids))
            .order_by(AiChatMessageVector.created_at.desc())
            .limit(limit)
            .all()
        )

    def delete_message_vectors_for_message(self, db: Session, message_id: int):
        db.query(AiChatMessageVector).filter(
            AiChatMessageVector.message_id == message_id
        ).delete()
        db.commit()

    # ─── 记忆 embedding ──────────────────────

    def update_memory_embedding(
        self, db: Session, memory_id: int, user_id: int, embedding: list[float]
    ) -> AiChatMemory | None:
        memory = self.get_memory(db, memory_id, user_id)
        if not memory:
            return None
        memory.embedding = json.dumps(embedding)
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    def list_active_memories_with_embedding(
        self, db: Session, user_id: int, limit: int = 100
    ) -> list[AiChatMemory]:
        return (
            db.query(AiChatMemory)
            .filter(
                AiChatMemory.user_id == user_id,
                AiChatMemory.is_active == True,
                AiChatMemory.embedding.isnot(None),
            )
            .order_by(AiChatMemory.created_at.desc())
            .limit(limit)
            .all()
        )


ai_chat_dao = AiChatDao()
