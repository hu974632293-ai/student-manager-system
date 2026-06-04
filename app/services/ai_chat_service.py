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
    memory_limit = max(1, int(os.getenv("AI_CHAT_MEMORY_LIMIT", "10")))
    client: QwenClient | None = None

    @staticmethod
    def get_client():
        if AiChatService.client is None:
            AiChatService.client = QwenClient()
        return AiChatService.client

    @staticmethod
    def chat(db: Session, payload: AiChatRequest, current_user=None):
        content = payload.message.strip()
        if not content:
            return fail("message is required")

        session_id = payload.session_id or uuid.uuid4().hex
        title = content[:50]

        try:
            user_id = current_user.id if current_user else None
            session = ai_chat_dao.get_session(db, session_id)
            if not session:
                ai_chat_dao.create_session(db, session_id, title)

            history = ai_chat_dao.list_recent_messages(db, session_id, AiChatService.context_limit)
            memories = ai_chat_dao.list_memories(db, user_id, AiChatService.memory_limit) if user_id else []
            saved_memory = AiChatService._extract_memory_content(content)
            if user_id and saved_memory:
                memory = ai_chat_dao.create_memory(db, user_id, saved_memory, source="auto")
                memories = ([memory] + [item for item in memories if item.id != memory.id])[: AiChatService.memory_limit]

            ai_chat_dao.create_message(db, session_id, "user", content)

            messages = AiChatService._build_memory_messages(memories)
            messages.extend({"role": item.role, "content": item.content} for item in history)
            messages.append({"role": "user", "content": content})
            reply = AiChatService.get_client().chat(messages)

            ai_chat_dao.create_message(db, session_id, "assistant", reply)
            ai_chat_dao.touch_session(db, session_id)

            return success(
                {
                    "session_id": session_id,
                    "reply": reply,
                    "context_message_count": len(history),
                    "memory_count": len(memories),
                    "saved_memory": saved_memory,
                }
            )
        except (SQLAlchemyError, QwenConfigError, QwenRequestError, QwenResponseError) as exc:
            db.rollback()
            return fail(str(exc))

    @staticmethod
    def list_memories(db: Session, current_user, limit: int = 20):
        safe_limit = min(max(int(limit), 1), 100)
        memories = ai_chat_dao.list_memories(db, current_user.id, safe_limit)
        return success(
            {
                "total": len(memories),
                "items": [AiChatService._memory_to_dict(memory) for memory in memories],
            },
            "memories found",
        )

    @staticmethod
    def create_memory(db: Session, payload, current_user):
        content = payload.content.strip()
        if not content:
            return fail("memory content is required")
        memory = ai_chat_dao.create_memory(db, current_user.id, content, source="manual")
        return success(AiChatService._memory_to_dict(memory), "memory created")

    @staticmethod
    def delete_memory(db: Session, memory_id: int, current_user):
        memory = ai_chat_dao.deactivate_memory(db, memory_id, current_user.id)
        if not memory:
            return fail("memory not found")
        return success(None, "memory deleted")

    @staticmethod
    def _build_memory_messages(memories) -> list[dict[str, str]]:
        if not memories:
            return []
        memory_lines = [f"{index}. {memory.content}" for index, memory in enumerate(reversed(memories), start=1)]
        content = (
            "以下是当前用户的长期记忆。回答时可以结合这些信息，但不要主动暴露记忆列表：\n"
            + "\n".join(memory_lines)
        )
        return [{"role": "system", "content": content}]

    @staticmethod
    def _extract_memory_content(message: str) -> str | None:
        text = message.strip()
        markers = ("请记住", "帮我记住", "记住一下", "记住", "remember")
        lowered_text = text.lower()
        for marker in markers:
            marker_index = lowered_text.find(marker.lower())
            if marker_index < 0:
                continue
            start_index = marker_index + len(marker)
            memory = text[start_index:].strip(" ：:，,。.\n\t")
            return memory[:1000] if memory else None
        return None

    @staticmethod
    def _memory_to_dict(memory) -> dict:
        return {
            "id": memory.id,
            "user_id": memory.user_id,
            "content": memory.content,
            "source": memory.source,
            "is_active": memory.is_active,
        }
