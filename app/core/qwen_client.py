import json
from typing import Any, Iterable
from urllib import error, request

from app.core.qwen_config import QwenConfig, QwenConfigError


class QwenRequestError(Exception):
    pass


class QwenResponseError(Exception):
    pass


QwenBaseError = (QwenConfigError, QwenRequestError, QwenResponseError)


class QwenClient:
    text_generation_path = "/services/aigc/text-generation/generation"
    image_generation_path = "/services/aigc/multimodal-generation/generation"
    embedding_path = "/services/embeddings/text-embedding/text-embedding"

    def __init__(self, config: QwenConfig | None = None):
        self.config = config or QwenConfig.from_env()

    def chat(
        self,
        messages: Iterable[dict[str, Any]],
        model: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        message_list = list(messages)
        if not message_list:
            raise QwenConfigError("messages is required")

        request_parameters = {"result_format": "message"}
        if parameters:
            request_parameters.update(parameters)

        payload = {
            "model": model or self.config.text_model,
            "input": {"messages": message_list},
            "parameters": request_parameters,
        }
        data = self._post(self.text_generation_path, payload)
        return self._parse_chat_content(data)

    def generate_image(
        self,
        prompt: str,
        model: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt_text = prompt.strip()
        if not prompt_text:
            raise QwenConfigError("prompt is required")

        payload = {
            "model": model or self.config.image_model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt_text}],
                    }
                ]
            },
        }
        if parameters:
            payload["parameters"] = parameters

        data = self._post(self.image_generation_path, payload)
        images = self._parse_image_urls(data)
        return {"images": images, "raw": data.get("output")}

    def embed_texts(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """批量文本向量化，返回与输入顺序对应的向量列表。

        DashScope text-embedding-v3 单次最多 6 条，超量会自动分批。
        """
        if not texts:
            raise QwenConfigError("texts is required")

        batch_size = 6
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            payload = {
                "model": model or self.config.embedding_model,
                "input": {"texts": batch},
            }
            data = self._post(self.embedding_path, payload)
            all_embeddings.extend(self._parse_embedding_response(data))

        return all_embeddings

    def embed_query(self, text: str, model: str | None = None) -> list[float]:
        """对单条查询文本向量化。"""
        return self.embed_texts([text], model=model)[0]

    def embed_documents(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """对文档列表向量化（与 embed_texts 行为一致）。"""
        return self.embed_texts(texts, model=model)

    def _parse_embedding_response(self, data: dict[str, Any]) -> list[list[float]]:
        """解析 embedding API 响应。"""
        output = data.get("output")
        if not isinstance(output, dict):
            raise QwenResponseError("Embedding response missing output")

        embeddings = output.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise QwenResponseError("Embedding response missing embeddings array")

        result: list[list[float]] = []
        for item in embeddings:
            if not isinstance(item, dict):
                raise QwenResponseError("Invalid embedding item in response")
            vec = item.get("embedding")
            if not isinstance(vec, list):
                raise QwenResponseError("Invalid embedding vector in response")
            result.append([float(v) for v in vec])
        return result

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        api_key = self.config.require_api_key()
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            f"{self.config.base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                status_code = getattr(response, "status", None) or response.getcode()
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            message = self._read_error_message(exc)
            raise QwenRequestError(f"Qwen request failed: HTTP {exc.code} {message}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise QwenRequestError(f"Qwen request failed: {exc}") from exc

        if status_code < 200 or status_code >= 300:
            raise QwenRequestError(f"Qwen request failed: HTTP {status_code}")

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise QwenResponseError("Qwen response is not valid JSON") from exc
        if not isinstance(data, dict):
            raise QwenResponseError("Qwen response must be a JSON object")
        return data

    def _read_error_message(self, exc: error.HTTPError) -> str:
        try:
            body = exc.read().decode("utf-8")
            data = json.loads(body)
        except Exception:
            return str(exc.reason)
        if isinstance(data, dict):
            return str(data.get("message") or data.get("code") or data)
        return str(data)

    def _parse_chat_content(self, data: dict[str, Any]) -> str:
        output = data.get("output")
        if not isinstance(output, dict):
            raise QwenResponseError("Qwen chat response missing output")

        choices = output.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message") if isinstance(choices[0], dict) else None
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content:
                    return content

        text = output.get("text") or data.get("content")
        if isinstance(text, str) and text:
            return text
        raise QwenResponseError("Qwen chat response content is empty")

    def _parse_image_urls(self, data: dict[str, Any]) -> list[str]:
        output = data.get("output")
        if not isinstance(output, dict):
            raise QwenResponseError("Qwen image response missing output")

        images: list[str] = []
        choices = output.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                message = choice.get("message")
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                if isinstance(content, list):
                    images.extend(self._extract_images_from_items(content))

        results = output.get("results")
        if isinstance(results, list):
            images.extend(self._extract_images_from_items(results))

        if not images:
            raise QwenResponseError("Qwen image response contains no image URL")
        return images

    def _extract_images_from_items(self, items: list[Any]) -> list[str]:
        images: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            image = item.get("image") or item.get("url") or item.get("image_url")
            if isinstance(image, str) and image:
                images.append(image)
        return images
