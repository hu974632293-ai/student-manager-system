import json
import logging
import os
import re
import uuid

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.qwen_client import QwenClient, QwenRequestError, QwenResponseError
from app.core.qwen_config import QwenConfigError
from app.core.response import fail, success
from app.core.token_estimator import TokenEstimator
from app.dao.ai_chat import ai_chat_dao
from app.services.ai_chat_compressor import ContextCompressor
from app.services.ai_chat_retriever import SemanticRetriever
from app.services.ai_chat_summarizer import SessionSummarizer
from app.views.schemas.ai_chat import AiChatRequest

logger = logging.getLogger(__name__)


class AiChatService:
    # ── 配置 ─────────────────────────────────
    context_limit = max(1, int(os.getenv("AI_CHAT_CONTEXT_LIMIT", "10")))
    memory_limit = max(1, int(os.getenv("AI_CHAT_MEMORY_LIMIT", "10")))
    max_tokens = max(1000, int(os.getenv("AI_CHAT_MAX_TOKENS", "6000")))
    compression_threshold = max(100, int(os.getenv("AI_CHAT_COMPRESSION_THRESHOLD", "4000")))
    retrieval_top_k = max(1, int(os.getenv("AI_CHAT_RETRIEVAL_TOP_K", "5")))
    retrieval_threshold = max(0.0, min(1.0, float(os.getenv("AI_CHAT_RETRIEVAL_THRESHOLD", "0.65"))))
    summary_min_messages = max(1, int(os.getenv("AI_CHAT_SUMMARY_MIN_MESSAGES", "20")))

    # ── 组件实例（懒加载单例）─────────────────
    client: QwenClient | None = None
    _summarizer: SessionSummarizer | None = None
    _compressor: ContextCompressor | None = None
    _retriever: SemanticRetriever | None = None

    # ═══════════════════════════════════════════
    #  组件初始化
    # ═══════════════════════════════════════════

    @classmethod
    def get_client(cls) -> QwenClient:
        if cls.client is None:
            cls.client = QwenClient()
        return cls.client

    @classmethod
    def _get_summarizer(cls) -> SessionSummarizer:
        if cls._summarizer is None:
            cls._summarizer = SessionSummarizer(cls.get_client())
        return cls._summarizer

    @classmethod
    def _get_compressor(cls) -> ContextCompressor:
        if cls._compressor is None:
            summarizer = cls._summarizer if cls._summarizer else cls._get_summarizer()
            cls._compressor = ContextCompressor(
                compression_threshold=cls.compression_threshold,
                summarizer=summarizer,
            )
        return cls._compressor

    @classmethod
    def _get_retriever(cls) -> SemanticRetriever:
        if cls._retriever is None:
            cls._retriever = SemanticRetriever(
                cls.get_client(),
                top_k=cls.retrieval_top_k,
                similarity_threshold=cls.retrieval_threshold,
            )
        return cls._retriever

    # ═══════════════════════════════════════════
    #  核心：chat()
    # ═══════════════════════════════════════════

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

            # 首次创建 session 时绑定 user_id
            if not session:
                ai_chat_dao.create_session(db, session_id, title, user_id=user_id)
            elif user_id and session.user_id and session.user_id != user_id:
                return fail("permission denied")
            elif user_id and not session.user_id:
                ai_chat_dao.set_session_user(db, session_id, user_id)

            # ── 1. 获取会话摘要 ──
            existing_summary = (
                ai_chat_dao.get_session_summary(db, session_id) or ""
            )

            # ── 2. 获取最近消息（多取一些用于压缩决策） ──
            fetch_limit = max(AiChatService.context_limit * 3, 30)
            history_messages = ai_chat_dao.list_recent_messages(
                db, session_id, fetch_limit
            )
            history_dicts = [
                {"role": item.role, "content": item.content}
                for item in history_messages
            ]

            # ── 3. 语义检索 ──
            retrieval_context = ""
            if user_id and content:
                retrieval_context = AiChatService._run_retrieval(db, user_id, content)

            # ── 4. 上下文压缩 ──
            compressor = AiChatService._get_compressor()
            compression_info = {"applied": False, "count": 0}
            if compressor.needs_compression(history_dicts):
                try:
                    ctx = compressor.compress(
                        history_dicts,
                        existing_summary=existing_summary,
                        session_summarizer=AiChatService._get_summarizer(),
                    )
                    history_dicts = ctx.recent_messages
                    if ctx.session_summary != existing_summary and ctx.session_summary:
                        ai_chat_dao.update_session_summary(
                            db, session_id, ctx.session_summary
                        )
                        existing_summary = ctx.session_summary
                    compression_info = {"applied": True, "count": ctx.summarized_count}
                except Exception as exc:
                    logger.warning("Context compression failed (will skip): %s", exc)

            # ── 5. 获取长期记忆 ──
            memories = (
                ai_chat_dao.list_memories(db, user_id, AiChatService.memory_limit)
                if user_id
                else []
            )
            saved_memory = AiChatService._extract_memory_content(content)
            if user_id and saved_memory:
                memory = ai_chat_dao.create_memory(db, user_id, saved_memory, source="auto")
                memories = ([memory] + [m for m in memories if m.id != memory.id])[
                    : AiChatService.memory_limit
                ]

            # ── 6. 存储用户消息（记录 token_count） ──
            user_token_count = TokenEstimator.estimate(content)
            msg_user = ai_chat_dao.create_message(db, session_id, "user", content)
            if msg_user.id:
                # 直接在 DB 更新 token_count
                from sqlalchemy import update as sa_update
                from app.models.ai_chat import AiChatMessage as MsgModel
                db.execute(
                    sa_update(MsgModel)
                    .where(MsgModel.id == msg_user.id)
                    .values(token_count=user_token_count)
                )
                db.commit()

            # ── 7. 构建 messages（system + history + current） ──
            messages = AiChatService._build_memory_messages(memories)

            # 会话摘要注入
            if existing_summary:
                messages.append({
                    "role": "system",
                    "content": f"当前会话摘要（仅参考历史背景，重点回应最新消息）：{existing_summary}",
                })

            # 检索结果注入
            if retrieval_context:
                messages.append({
                    "role": "system",
                    "content": retrieval_context,
                })

            messages.extend(history_dicts)
            messages.append({"role": "user", "content": content})

            # ── 8. 调用 Qwen ──
            reply = AiChatService.get_client().chat(messages)
            msg_assistant = ai_chat_dao.create_message(db, session_id, "assistant", reply)
            ai_chat_dao.touch_session(db, session_id)

            # ── 9. 后处理（embedding + 摘要检查，失败不影响主流程） ──
            _post_process_msg = msg_user.id if msg_user else None
            if _post_process_msg and user_id:
                try:
                    AiChatService._store_message_embedding(
                        db, msg_user.id, session_id, content
                    )
                except Exception as exc:
                    logger.warning("Failed to store message embedding: %s", exc)

            # 检查是否需要自动摘要
            if existing_summary and compression_info["applied"]:
                pass  # 压缩时已更新摘要
            elif (
                existing_summary
                and len(history_dicts) + 2 >= AiChatService.summary_min_messages
            ):
                try:
                    all_msgs = ai_chat_dao.list_all_session_messages(db, session_id)
                    all_dicts = [
                        {"role": m.role, "content": m.content} for m in all_msgs
                    ]
                    summarizer = AiChatService._get_summarizer()
                    new_summary = summarizer.update_summary(existing_summary, all_dicts[-10:])
                    if new_summary and new_summary != existing_summary:
                        ai_chat_dao.update_session_summary(db, session_id, new_summary)
                except Exception as exc:
                    logger.warning("Auto-summary update failed: %s", exc)

            return success(
                {
                    "session_id": session_id,
                    "reply": reply,
                    "context_message_count": len(history_dicts),
                    "memory_count": len(memories),
                    "saved_memory": saved_memory,
                    "compression_applied": compression_info["applied"],
                    "compression_count": compression_info["count"],
                    "retrieval_count": AiChatService._count_retrieval_context(retrieval_context),
                }
            )

        except (SQLAlchemyError, QwenConfigError, QwenRequestError, QwenResponseError) as exc:
            db.rollback()
            logger.exception("Chat error")
            return fail(str(exc))

    # ═══════════════════════════════════════════
    #  内部助手
    # ═══════════════════════════════════════════

    @classmethod
    def _run_retrieval(cls, db: Session, user_id: int, query: str) -> str:
        """执行语义检索，返回格式化后的上下文文本。"""
        try:
            # 获取用户最近的会话
            session_ids = ai_chat_dao.list_user_session_ids(db, user_id, limit=10)
            if not session_ids:
                return ""

            # 加载候选向量
            message_vectors_raw = ai_chat_dao.list_message_vectors_by_sessions(
                db, session_ids, limit=200
            )
            message_vectors = [
                {
                    "message_id": mv.message_id,
                    "session_id": mv.session_id,
                    "content_text": mv.content_text,
                    "embedding": mv.embedding,
                }
                for mv in message_vectors_raw
            ]

            memories_raw = ai_chat_dao.list_active_memories_with_embedding(
                db, user_id, limit=100
            )
            memories_with_embedding = [
                {
                    "id": mem.id,
                    "content": mem.content,
                    "embedding": mem.embedding,
                }
                for mem in memories_raw
            ]

            if not message_vectors and not memories_with_embedding:
                return ""

            retriever = cls._get_retriever()
            results = retriever.retrieve(query, message_vectors, memories_with_embedding)
            return retriever.format_context(results) if results else ""
        except Exception as exc:
            logger.warning("Semantic retrieval failed (will skip): %s", exc)
            return ""

    @staticmethod
    def _count_retrieval_context(context: str) -> int:
        if not context:
            return 0
        return len(re.findall(r"(?m)^\d+\.\s+", context))

    @classmethod
    def _store_message_embedding(
        cls, db: Session, message_id: int, session_id: str, content: str
    ):
        """为消息生成 embedding 并存储。"""
        if not content.strip():
            return
        client = cls.get_client()
        embedding = client.embed_query(content)
        ai_chat_dao.create_message_vector(
            db,
            message_id=message_id,
            session_id=session_id,
            content_text=content[:500],
            embedding=embedding,
        )

    # ═══════════════════════════════════════════
    #  记忆管理（保留原有逻辑）
    # ═══════════════════════════════════════════

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
        # 异步生成 embedding
        try:
            embedding = AiChatService.get_client().embed_query(content)
            ai_chat_dao.update_memory_embedding(db, memory.id, current_user.id, embedding)
        except Exception as exc:
            logger.warning("Failed to embed new memory: %s", exc)
        return success(AiChatService._memory_to_dict(memory), "memory created")

    @staticmethod
    def delete_memory(db: Session, memory_id: int, current_user):
        memory = ai_chat_dao.deactivate_memory(db, memory_id, current_user.id)
        if not memory:
            return fail("memory not found")
        return success(None, "memory deleted")

    @staticmethod
    def _can_access_session(session, current_user) -> bool:
        if not session:
            return False
        if current_user is None:
            return True
        return session.user_id in (None, current_user.id)

    @staticmethod
    def _claim_session_if_needed(db: Session, session, current_user):
        if session and current_user is not None and session.user_id is None:
            return ai_chat_dao.set_session_user(db, session.session_id, current_user.id)
        return session

    @staticmethod
    def _format_datetime(value) -> str | None:
        return value.isoformat() if value else None

    @staticmethod
    def _session_to_dict(session) -> dict:
        messages = list(session.messages or [])
        last_message = messages[-1].content if messages else ""
        return {
            "id": session.id,
            "session_id": session.session_id,
            "title": session.title or last_message[:30] or "新对话",
            "summary": session.summary,
            "summary_updated_at": AiChatService._format_datetime(session.summary_updated_at),
            "created_at": AiChatService._format_datetime(session.created_at),
            "updated_at": AiChatService._format_datetime(session.updated_at),
            "message_count": len(messages),
            "last_message": last_message[:120],
        }

    @staticmethod
    def _message_to_dict(message) -> dict:
        return {
            "id": message.id,
            "session_id": message.session_id,
            "role": message.role,
            "content": message.content,
            "created_at": AiChatService._format_datetime(message.created_at),
        }

    @staticmethod
    def create_session(db: Session, payload, current_user):
        title = (payload.title or "").strip() or "新对话"
        session_id = uuid.uuid4().hex
        session = ai_chat_dao.create_session(db, session_id, title[:100], user_id=current_user.id)
        return success(AiChatService._session_to_dict(session), "session created")

    @staticmethod
    def list_sessions(db: Session, current_user, keyword: str = None, limit: int = 50):
        safe_limit = min(max(int(limit), 1), 100)
        safe_keyword = keyword.strip() if keyword else None
        sessions = ai_chat_dao.list_user_sessions(db, current_user.id, safe_keyword, safe_limit)
        return success(
            {
                "total": len(sessions),
                "items": [AiChatService._session_to_dict(session) for session in sessions],
            },
            "sessions found",
        )

    @staticmethod
    def update_session(db: Session, session_id: str, payload, current_user):
        title = payload.title.strip()
        if not title:
            return fail("title is required")
        session = ai_chat_dao.update_session_title(db, session_id, current_user.id, title[:100])
        if not session:
            return fail("session not found")
        return success(AiChatService._session_to_dict(session), "session updated")

    @staticmethod
    def delete_session(db: Session, session_id: str, current_user):
        if not ai_chat_dao.delete_session(db, session_id, current_user.id):
            return fail("session not found")
        return success(None, "session deleted")

    @staticmethod
    def get_session_messages(db: Session, session_id: str, current_user):
        session = ai_chat_dao.get_session(db, session_id)
        if not AiChatService._can_access_session(session, current_user):
            return fail("permission denied")
        session = AiChatService._claim_session_if_needed(db, session, current_user)
        messages = ai_chat_dao.list_all_session_messages(db, session_id)
        return success(
            {
                "session": AiChatService._session_to_dict(session),
                "items": [AiChatService._message_to_dict(message) for message in messages],
            },
            "messages found",
        )

    # ═══════════════════════════════════════════
    #  新增 API：会话摘要
    # ═══════════════════════════════════════════

    @staticmethod
    def get_session_summary(db: Session, session_id: str, current_user=None):
        session = ai_chat_dao.get_session(db, session_id)
        if not AiChatService._can_access_session(session, current_user):
            return fail("permission denied")
        session = AiChatService._claim_session_if_needed(db, session, current_user)
        if not session:
            return fail("session not found")
        return success({
            "session_id": session.session_id,
            "summary": session.summary,
            "summary_updated_at": session.summary_updated_at.isoformat()
                if session.summary_updated_at else None,
            "message_count": len(session.messages) if session.messages else 0,
        })

    @staticmethod
    def regenerate_summary(db: Session, session_id: str, current_user=None):
        """一次性全量扫描会话消息，重新生成摘要。"""
        session = ai_chat_dao.get_session(db, session_id)
        if not AiChatService._can_access_session(session, current_user):
            return fail("permission denied")
        session = AiChatService._claim_session_if_needed(db, session, current_user)
        if not session:
            return fail("session not found")

        messages = ai_chat_dao.list_all_session_messages(db, session_id)
        if not messages:
            return success({"session_id": session_id, "summary": ""}, "no messages to summarize")

        msg_dicts = [{"role": m.role, "content": m.content} for m in messages]
        try:
            summarizer = AiChatService._get_summarizer()
            summary = summarizer.generate_summary(msg_dicts)
            if summary:
                ai_chat_dao.update_session_summary(db, session_id, summary)
            return success({
                "session_id": session_id,
                "summary": summary,
                "message_count": len(messages),
            })
        except Exception as exc:
            logger.exception("Failed to regenerate summary")
            return fail(str(exc))

    # ═══════════════════════════════════════════
    #  新增 API：语义搜索
    # ═══════════════════════════════════════════

    @staticmethod
    def search_memories(db: Session, query: str, user_id: int, limit: int = 5):
        if not query.strip():
            return fail("query is required")
        try:
            retriever = AiChatService._get_retriever()
            query_vec = AiChatService.get_client().embed_query(query)

            memories_raw = ai_chat_dao.list_active_memories_with_embedding(db, user_id, limit=100)
            memories_with_embedding = [
                {"id": m.id, "content": m.content, "embedding": m.embedding}
                for m in memories_raw if m.embedding
            ]

            if not memories_with_embedding:
                return success({"query": query, "total": 0, "items": []})

            import numpy as np
            mem_embeddings = [
                (json.loads(m["embedding"]) if isinstance(m["embedding"], str)
                 else m["embedding"])
                for m in memories_with_embedding
            ]
            mem_vecs = np.array(mem_embeddings, dtype=np.float32)
            qv = np.array(query_vec, dtype=np.float32)
            sims = retriever._cosine_similarity(qv, mem_vecs)

            items = []
            for i in range(len(sims)):
                if sims[i] >= 0.5:
                    m = memories_with_embedding[i]
                    items.append({
                        "id": m["id"],
                        "content": m["content"],
                        "similarity": float(sims[i]),
                    })
            items.sort(key=lambda x: x["similarity"], reverse=True)
            items = items[:limit]

            return success({"query": query, "total": len(items), "items": items})
        except Exception as exc:
            logger.exception("Memory search failed")
            return fail(str(exc))

    # ═══════════════════════════════════════════
    #  工具方法（原样保留）
    # ═══════════════════════════════════════════

    @staticmethod
    def _build_memory_messages(memories) -> list[dict[str, str]]:
        if not memories:
            return []
        memory_lines = [
            f"{index}. {memory.content}"
            for index, memory in enumerate(reversed(memories), start=1)
        ]
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
