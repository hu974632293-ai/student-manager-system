import json
from typing import Any, Iterable
from urllib import error, request

from app.core.ollama_config import OllamaConfig


class OllamaRequestError(Exception):
    pass


class OllamaResponseError(Exception):
    pass


class OllamaClient:
    generate_path = "/api/generate"
    chat_path = "/api/chat"

    def __init__(self, config: OllamaConfig | None = None):
        self.config = config or OllamaConfig.from_env()

    def generate(self, prompt: str, model: str | None = None) -> str:
        content = prompt.strip()
        if not content:
            raise OllamaRequestError("prompt is required")

        payload = {
            "model": model or self.config.model,
            "prompt": content,
            "stream": False,
        }
        data = self._post(self.generate_path, payload)
        response = data.get("response")
        if not isinstance(response, str) or not response.strip():
            raise OllamaResponseError("Ollama generate response content is empty")
        return response.strip()

    def chat(self, messages: Iterable[dict[str, Any]], model: str | None = None) -> str:
        message_list = list(messages)
        if not message_list:
            raise OllamaRequestError("messages is required")

        payload = {
            "model": model or self.config.model,
            "messages": message_list,
            "stream": False,
        }
        data = self._post(self.chat_path, payload)
        message = data.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
        raise OllamaResponseError("Ollama chat response content is empty")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            f"{self.config.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                status_code = getattr(response, "status", None) or response.getcode()
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            message = self._read_error_message(exc)
            raise OllamaRequestError(f"Ollama request failed: HTTP {exc.code} {message}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise OllamaRequestError(f"Ollama request failed: {exc}") from exc

        if status_code < 200 or status_code >= 300:
            raise OllamaRequestError(f"Ollama request failed: HTTP {status_code}")

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise OllamaResponseError("Ollama response is not valid JSON") from exc
        if not isinstance(data, dict):
            raise OllamaResponseError("Ollama response must be a JSON object")
        return data

    def _read_error_message(self, exc: error.HTTPError) -> str:
        try:
            body = exc.read().decode("utf-8")
            data = json.loads(body)
        except Exception:
            return str(exc.reason)
        if isinstance(data, dict):
            return str(data.get("error") or data)
        return str(data)
