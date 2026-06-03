from app.core.ollama_client import OllamaClient, OllamaRequestError, OllamaResponseError
from app.core.ollama_config import OllamaConfigError
from app.core.response import fail, success
from app.utils.email_util import EmailConfigError, EmailSendError, send_email
from app.views.schemas.letter import LetterGenerateRequest, LetterSendRequest


RECIPIENT_NAMES = {
    "luke": "Luke哥",
    "assistant_teacher": "助教老师",
    "head_teacher": "班主任",
}


class LetterService:
    client: OllamaClient | None = None

    @staticmethod
    def get_client() -> OllamaClient:
        if LetterService.client is None:
            LetterService.client = OllamaClient()
        return LetterService.client

    @staticmethod
    def generate_letter(payload: LetterGenerateRequest):
        try:
            content = LetterService._generate_letter_content(payload)
            return success(
                {
                    "recipient": payload.recipient,
                    "recipient_name": RECIPIENT_NAMES[payload.recipient],
                    "method": payload.method,
                    "content": content,
                }
            )
        except (OllamaConfigError, OllamaRequestError, OllamaResponseError) as exc:
            return fail(str(exc))

    @staticmethod
    def send_letter(payload: LetterSendRequest):
        try:
            content = LetterService._generate_letter_content(payload)
            subject = payload.subject or f"写给{RECIPIENT_NAMES[payload.recipient]}的一封信"
            send_email(str(payload.to_email), subject, content)
            return success(
                {
                    "recipient": payload.recipient,
                    "recipient_name": RECIPIENT_NAMES[payload.recipient],
                    "to_email": str(payload.to_email),
                    "subject": subject,
                    "method": payload.method,
                    "content": content,
                }
            )
        except (OllamaConfigError, OllamaRequestError, OllamaResponseError, EmailConfigError, EmailSendError) as exc:
            return fail(str(exc))

    @staticmethod
    def _generate_letter_content(payload: LetterGenerateRequest) -> str:
        recipient_name = RECIPIENT_NAMES[payload.recipient]
        tone = payload.tone.strip() if payload.tone else "真诚、礼貌、自然"
        prompt = (
            f"请给{recipient_name}写一封中文信。"
            f"主题：{payload.topic.strip()}。"
            f"语气：{tone}。"
            "要求：格式完整，包含称呼、正文、结尾和署名，不要输出解释。"
        )
        client = LetterService.get_client()
        if payload.method == "generate":
            return client.generate(prompt)
        return client.chat([{"role": "user", "content": prompt}])
