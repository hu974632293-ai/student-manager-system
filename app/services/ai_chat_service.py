import os
import uuid

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.qwen_client import QwenClient, QwenRequestError, QwenResponseError
from app.core.qwen_config import QwenConfigError
from app.core.response import fail, success
from app.dao.ai_chat import ai_chat_dao
from app.views.schemas.ai_chat import AiChatRequest


class AiChatService:
    context_limit = max(1, int(os.getenv("AI_CHAT_CONTEXT_LIMIT", "10")))
    client: QwenClient | None = None

    @staticmethod
    def get_client():
        if AiChatService.client is None:
            AiChatService.client = QwenClient()
        return AiChatService.client

    @staticmethod
    def chat(db: Session, payload: AiChatRequest):
        content = payload.message.strip()
        if not content:
            return fail("message is required")

        session_id = payload.session_id or uuid.uuid4().hex
        title = content[:50]

        try:
            session = ai_chat_dao.get_session(db, session_id)
            if not session:
                ai_chat_dao.create_session(db, session_id, title)

            history = ai_chat_dao.list_recent_messages(db, session_id, AiChatService.context_limit)
            ai_chat_dao.create_message(db, session_id, "user", content)

            messages = [{"role": item.role, "content": item.content} for item in history]
            messages.append({"role": "user", "content": content})
            reply = AiChatService.get_client().chat(messages)

            ai_chat_dao.create_message(db, session_id, "assistant", reply)
            ai_chat_dao.touch_session(db, session_id)

            return success(
                {
                    "session_id": session_id,
                    "reply": reply,
                    "context_message_count": len(history),
                }
            )
        except (SQLAlchemyError, QwenConfigError, QwenRequestError, QwenResponseError) as exc:
            db.rollback()
            return fail(str(exc))
