from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ai_chat_service import AiChatService
from app.views.schemas.ai_chat import AiChatRequest


ai_chat_router = APIRouter(prefix="/ai", tags=["ai"])


@ai_chat_router.post("/chat", summary="与 AI 助手进行对话")
def chat(payload: AiChatRequest, db: Session = Depends(get_db)):
    return AiChatService.chat(db, payload)
