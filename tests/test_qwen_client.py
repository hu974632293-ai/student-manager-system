import json

import pytest

from app.core.qwen_client import QwenClient, QwenRequestError, QwenResponseError
from app.core.qwen_config import QwenConfig, QwenConfigError


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


def make_client(api_key="test-key"):
    return QwenClient(
        QwenConfig(
            api_key=api_key,
            text_model="qwen-plus",
            image_model="qwen-image-2.0-pro",
            embedding_model="text-embedding-v3",
            base_url="https://dashscope.aliyuncs.com/api/v1",
            timeout_seconds=30,
        )
    )


def test_chat_requires_api_key():
    client = make_client(api_key=None)

    with pytest.raises(QwenConfigError, match="QWEN_API_KEY or DASHSCOPE_API_KEY is required"):
        client.chat([{"role": "user", "content": "hello"}])


def test_generate_image_requires_api_key():
    client = make_client(api_key=None)

    with pytest.raises(QwenConfigError, match="QWEN_API_KEY or DASHSCOPE_API_KEY is required"):
        client.generate_image("create an image")


def test_chat_parses_dashscope_message(monkeypatch):
    from app.core import qwen_client

    payload = {
        "output": {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "hello from Qwen",
                    }
                }
            ]
        }
    }
    monkeypatch.setattr(qwen_client.request, "urlopen", lambda req, timeout: FakeResponse(payload))

    assert make_client().chat([{"role": "user", "content": "hello"}]) == "hello from Qwen"


def test_generate_image_parses_image_url(monkeypatch):
    from app.core import qwen_client

    payload = {
        "output": {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"image": "https://example.com/image.png"},
                        ]
                    }
                }
            ]
        }
    }
    monkeypatch.setattr(qwen_client.request, "urlopen", lambda req, timeout: FakeResponse(payload))

    result = make_client().generate_image("create an image")

    assert result["images"] == ["https://example.com/image.png"]


def test_invalid_json_raises_response_error(monkeypatch):
    from app.core import qwen_client

    monkeypatch.setattr(qwen_client.request, "urlopen", lambda req, timeout: FakeResponse(b"not-json"))

    with pytest.raises(QwenResponseError, match="not valid JSON"):
        make_client().chat([{"role": "user", "content": "hello"}])


def test_network_error_raises_request_error(monkeypatch):
    from app.core import qwen_client
    from urllib import error

    def fake_urlopen(req, timeout):
        raise error.URLError("network unavailable")

    monkeypatch.setattr(qwen_client.request, "urlopen", fake_urlopen)

    with pytest.raises(QwenRequestError, match="Qwen request failed"):
        make_client().chat([{"role": "user", "content": "hello"}])


def test_ai_chat_service_returns_unified_failure(monkeypatch):
    from app.services.ai_chat_service import AiChatService
    from app.views.schemas.ai_chat import AiChatRequest

    class FakeMessage:
        id = None

    class FakeDao:
        def get_session(self, db, session_id):
            return None

        def create_session(self, db, session_id, title):
            return object()

        def get_session_summary(self, db, session_id):
            return None

        def list_recent_messages(self, db, session_id, limit):
            return []

        def create_message(self, db, session_id, role, content):
            return FakeMessage()

        def list_memories(self, db, user_id, limit):
            return []

    class FakeClient:
        def chat(self, messages):
            raise QwenConfigError("QWEN_API_KEY or DASHSCOPE_API_KEY is required")

    class FakeDb:
        def rollback(self):
            self.rolled_back = True

    from app.services import ai_chat_service

    fake_db = FakeDb()
    monkeypatch.setattr(ai_chat_service, "ai_chat_dao", FakeDao())
    monkeypatch.setattr(AiChatService, "client", FakeClient())

    result = AiChatService.chat(fake_db, AiChatRequest(message="hello"))

    assert result == {
        "code": 0,
        "msg": "未配置通义千问 API Key，请先配置 QWEN_API_KEY 或 DASHSCOPE_API_KEY",
        "data": None,
    }
    assert fake_db.rolled_back is True


def test_ai_chat_service_injects_user_memory(monkeypatch):
    from app.services.ai_chat_service import AiChatService
    from app.views.schemas.ai_chat import AiChatRequest

    class FakeSession:
        user_id = 7

    class FakeMessage:
        id = None

    class FakeMemory:
        id = 1
        content = "用户喜欢简洁回答"

    class FakeDao:
        def get_session(self, db, session_id):
            return FakeSession()

        def get_session_summary(self, db, session_id):
            return None

        def list_recent_messages(self, db, session_id, limit):
            return []

        def list_memories(self, db, user_id, limit):
            return [FakeMemory()]

        def create_message(self, db, session_id, role, content):
            return FakeMessage()

        def touch_session(self, db, session_id):
            return object()

        def list_user_session_ids(self, db, user_id, limit=10):
            return []

    class FakeClient:
        captured_messages = None

        def chat(self, messages):
            self.captured_messages = messages
            return "ok"

    class FakeUser:
        id = 7

    from app.services import ai_chat_service

    fake_client = FakeClient()
    monkeypatch.setattr(ai_chat_service, "ai_chat_dao", FakeDao())
    monkeypatch.setattr(AiChatService, "client", fake_client)

    result = AiChatService.chat(object(), AiChatRequest(session_id="s1", message="hello"), current_user=FakeUser())

    assert result["code"] == 1
    assert result["data"]["memory_count"] == 1
    assert fake_client.captured_messages[0]["role"] == "system"
    assert "用户喜欢简洁回答" in fake_client.captured_messages[0]["content"]


def test_ai_chat_service_saves_explicit_memory(monkeypatch):
    from app.services.ai_chat_service import AiChatService
    from app.views.schemas.ai_chat import AiChatRequest

    class FakeSession:
        user_id = 7

    class FakeMessage:
        id = None

    class FakeMemory:
        id = 2
        content = "我的专业是软件工程"

    class FakeDao:
        saved_content = None

        def get_session(self, db, session_id):
            return FakeSession()

        def get_session_summary(self, db, session_id):
            return None

        def list_recent_messages(self, db, session_id, limit):
            return []

        def list_memories(self, db, user_id, limit):
            return []

        def create_memory(self, db, user_id, content, source="manual"):
            self.saved_content = content
            return FakeMemory()

        def create_message(self, db, session_id, role, content):
            return FakeMessage()

        def touch_session(self, db, session_id):
            return object()

        def list_user_session_ids(self, db, user_id, limit=10):
            return []

    class FakeClient:
        def chat(self, messages):
            return "我记住了"

    class FakeUser:
        id = 7

    from app.services import ai_chat_service

    fake_dao = FakeDao()
    monkeypatch.setattr(ai_chat_service, "ai_chat_dao", fake_dao)
    monkeypatch.setattr(AiChatService, "client", FakeClient())

    result = AiChatService.chat(object(), AiChatRequest(session_id="s1", message="请记住我的专业是软件工程"), current_user=FakeUser())

    assert result["code"] == 1
    assert result["data"]["saved_memory"] == "我的专业是软件工程"
    assert fake_dao.saved_content == "我的专业是软件工程"
