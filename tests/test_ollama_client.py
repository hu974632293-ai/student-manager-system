import json

from app.core.ollama_client import OllamaClient
from app.core.ollama_config import OllamaConfig
from app.services.letter_service import LetterService
from app.views.schemas.letter import LetterGenerateRequest


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getcode(self):
        return self.status

    def read(self):
        if isinstance(self.payload, bytes):
            return self.payload
        return json.dumps(self.payload).encode("utf-8")


def make_client():
    return OllamaClient(
        OllamaConfig(
            base_url="http://127.0.0.1:11434",
            model="llama3.1",
            timeout_seconds=60,
        )
    )


def test_generate_posts_to_ollama_generate(monkeypatch):
    from app.core import ollama_client

    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse({"response": "生成结果"})

    monkeypatch.setattr(ollama_client.request, "urlopen", fake_urlopen)

    assert make_client().generate("请写信") == "生成结果"
    assert captured["url"] == "http://127.0.0.1:11434/api/generate"
    assert captured["body"]["model"] == "llama3.1"
    assert captured["body"]["prompt"] == "请写信"
    assert captured["body"]["stream"] is False
    assert captured["timeout"] == 60


def test_chat_posts_to_ollama_chat(monkeypatch):
    from app.core import ollama_client

    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return FakeResponse({"message": {"role": "assistant", "content": "聊天结果"}})

    monkeypatch.setattr(ollama_client.request, "urlopen", fake_urlopen)

    assert make_client().chat([{"role": "user", "content": "请写信"}]) == "聊天结果"
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["body"]["messages"] == [{"role": "user", "content": "请写信"}]
    assert captured["body"]["stream"] is False


def test_letter_service_returns_unified_success(monkeypatch):
    class FakeClient:
        def chat(self, messages):
            assert "Luke哥" in messages[0]["content"]
            return "Luke哥：\n这是正文。"

    monkeypatch.setattr(LetterService, "client", FakeClient())

    result = LetterService.generate_letter(
        LetterGenerateRequest(recipient="luke", topic="感谢指导")
    )

    assert result == {
        "code": 1,
        "msg": "success",
        "data": {
            "recipient": "luke",
            "recipient_name": "Luke哥",
            "method": "chat",
            "content": "Luke哥：\n这是正文。",
        },
    }
