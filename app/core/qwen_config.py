import os
from dataclasses import dataclass

from dotenv import load_dotenv


DEFAULT_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
DEFAULT_QWEN_TEXT_MODEL = "qwen-plus"
DEFAULT_QWEN_IMAGE_MODEL = "qwen-image-2.0-pro"
DEFAULT_QWEN_TIMEOUT_SECONDS = 30


class QwenConfigError(Exception):
    pass


@dataclass(frozen=True)
class QwenConfig:
    api_key: str | None
    text_model: str
    image_model: str
    base_url: str
    timeout_seconds: int

    @classmethod
    def from_env(cls) -> "QwenConfig":
        load_dotenv()
        timeout_value = os.getenv("QWEN_TIMEOUT_SECONDS", str(DEFAULT_QWEN_TIMEOUT_SECONDS))
        try:
            timeout_seconds = int(timeout_value)
        except ValueError as exc:
            raise QwenConfigError("QWEN_TIMEOUT_SECONDS must be an integer") from exc
        if timeout_seconds <= 0:
            raise QwenConfigError("QWEN_TIMEOUT_SECONDS must be greater than 0")

        return cls(
            api_key=os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY"),
            text_model=os.getenv("QWEN_TEXT_MODEL") or os.getenv("AI_CHAT_MODEL") or DEFAULT_QWEN_TEXT_MODEL,
            image_model=os.getenv("QWEN_IMAGE_MODEL", DEFAULT_QWEN_IMAGE_MODEL),
            base_url=os.getenv("QWEN_BASE_URL", DEFAULT_QWEN_BASE_URL).rstrip("/"),
            timeout_seconds=timeout_seconds,
        )

    def require_api_key(self) -> str:
        if not self.api_key:
            raise QwenConfigError("QWEN_API_KEY or DASHSCOPE_API_KEY is required")
        return self.api_key
