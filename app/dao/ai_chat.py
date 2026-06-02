from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ai_chat import AiChatMessage, AiChatSession


class AiChatDao:
    def get_session(self, db: Session, session_id: str):
        return db.query(AiChatSession).filter(AiChatSession.session_id == session_id).first()

    def create_session(self, db: Session, session_id: str, title: str = None):
        session = AiChatSession(session_id=session_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

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


ai_chat_dao = AiChatDao()
