import os
from dataclasses import dataclass

from dotenv import load_dotenv


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 60


class OllamaConfigError(Exception):
    pass


@dataclass(frozen=True)
class OllamaConfig:
    base_url: str
    model: str
    timeout_seconds: int

    @classmethod
    def from_env(cls) -> "OllamaConfig":
        load_dotenv()
        timeout_value = os.getenv("OLLAMA_TIMEOUT_SECONDS", str(DEFAULT_OLLAMA_TIMEOUT_SECONDS))
        try:
            timeout_seconds = int(timeout_value)
        except ValueError as exc:
            raise OllamaConfigError("OLLAMA_TIMEOUT_SECONDS must be an integer") from exc
        if timeout_seconds <= 0:
            raise OllamaConfigError("OLLAMA_TIMEOUT_SECONDS must be greater than 0")

        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).rstrip("/"),
            model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            timeout_seconds=timeout_seconds,
        )
