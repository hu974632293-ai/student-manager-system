from fastapi import APIRouter, Depends

from app.controllers.auth import require_roles
from app.services.letter_service import LetterService
from app.views.schemas.letter import LetterGenerateRequest, LetterSendRequest


letter_router = APIRouter(prefix="/letters", tags=["letters"])


@letter_router.post("/generate", summary="调用本地大模型生成信件内容")
def generate_letter(
    payload: LetterGenerateRequest,
    current_user=Depends(require_roles("admin", "teacher", "consultant")),
):
    return LetterService.generate_letter(payload)


@letter_router.post("/send", summary="调用本地大模型生成信件内容并发送到邮箱")
def send_letter(
    payload: LetterSendRequest,
    current_user=Depends(require_roles("admin", "teacher", "consultant")),
):
    return LetterService.send_letter(payload)
