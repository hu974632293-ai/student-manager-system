from fastapi import APIRouter

from app.services.letter_service import LetterService
from app.views.schemas.letter import LetterGenerateRequest, LetterSendRequest


letter_router = APIRouter(prefix="/letters", tags=["letters"])


@letter_router.post("/generate")
def generate_letter(payload: LetterGenerateRequest):
    return LetterService.generate_letter(payload)


@letter_router.post("/send")
def send_letter(payload: LetterSendRequest):
    return LetterService.send_letter(payload)
