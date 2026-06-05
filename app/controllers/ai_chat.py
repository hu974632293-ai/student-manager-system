from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.controllers.auth import require_roles
from app.services.ai_chat_service import AiChatService
from app.views.schemas.ai_chat import AiChatMemoryCreateRequest, AiChatRequest


ai_chat_router = APIRouter(prefix="/ai", tags=["ai"])


@ai_chat_router.post("/chat", summary="与 AI 助手进行对话")
def chat(
    payload: AiChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher", "student", "consultant")),
):
    return AiChatService.chat(db, payload, current_user=current_user)


@ai_chat_router.get("/memories", summary="查询 AI 长期记忆")
def list_memories(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher", "student", "consultant")),
):
    return AiChatService.list_memories(db, current_user, limit)


@ai_chat_router.post("/memories", summary="添加 AI 长期记忆")
def create_memory(
    payload: AiChatMemoryCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher", "student", "consultant")),
):
    return AiChatService.create_memory(db, payload, current_user)


@ai_chat_router.delete("/memories/{memory_id}", summary="删除 AI 长期记忆")
def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher", "student", "consultant")),
):
    return AiChatService.delete_memory(db, memory_id, current_user)


@ai_chat_router.get("/sessions/{session_id}/summary", summary="获取 AI 会话摘要")
def get_session_summary(
    session_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher", "student", "consultant")),
):
    return AiChatService.get_session_summary(db, session_id)


@ai_chat_router.post("/sessions/{session_id}/summarize", summary="重新生成会话摘要")
def regenerate_summary(
    session_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher", "student", "consultant")),
):
    return AiChatService.regenerate_summary(db, session_id)


@ai_chat_router.get("/memories/search", summary="语义搜索长期记忆")
def search_memories(
    q: str = Query(..., min_length=1, max_length=500, description="搜索关键词或问题"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "teacher", "student", "consultant")),
):
    return AiChatService.search_memories(db, q, current_user.id, limit)
