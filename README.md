# Student Manager System

FastAPI + Vue static frontend student management system.

## Project Layout

- `app/main.py`: FastAPI application factory, route registration, static frontend mounting.
- `app/controllers/`: MVC controller layer, implemented as FastAPI routers. Controllers call services only.
- `app/models/`: SQLAlchemy ORM models.
- `app/views/schemas/`: Pydantic request and response schemas.
- `app/dao/`: database CRUD/query layer.
- `app/services/`: business service layer for validation, orchestration, and API response assembly.
- `app/core/`: infrastructure code such as database setup, response helpers, and exception handlers.
- `frontend/`: static Vue + Element Plus frontend served by FastAPI.
- `tests/`: Python and frontend verification scripts.
- `scripts/`: database and presentation helper scripts.

## Run

```powershell
python main.py
```

The compatibility entrypoint still exposes `main:app`, so existing `uvicorn main:app --host 127.0.0.1 --port 8088` commands continue to work.

## API Response

Backend APIs return a unified structure:

```json
{
  "code": 1,
  "msg": "success",
  "data": null
}
```

## AI Chat API

`POST /ai/chat` creates or continues an AI chat session. Request body:

```json
{
  "session_id": "optional-existing-session-id",
  "message": "你好"
}
```

The service stores user and assistant messages in `ai_chat_sessions` and `ai_chat_messages`, then uses the latest `AI_CHAT_CONTEXT_LIMIT` messages as context. Third-party model calls are handled by `app/core/qwen_client.py`, so controller and DAO code do not call DashScope directly.

Configure Qwen/DashScope with environment variables:

- `QWEN_API_KEY`: DashScope API Key. `DASHSCOPE_API_KEY` is also accepted for compatibility.
- `QWEN_TEXT_MODEL`: text chat model, default `qwen-plus`. `AI_CHAT_MODEL` is accepted as a compatibility fallback.
- `QWEN_IMAGE_MODEL`: image model, default `qwen-image-2.0-pro`.
- `QWEN_BASE_URL`: DashScope base URL, default `https://dashscope.aliyuncs.com/api/v1`.
- `QWEN_TIMEOUT_SECONDS`: request timeout, default `30`.
- `AI_CHAT_CONTEXT_LIMIT`: number of recent chat messages used as context, default `10`.

Do not write real API Keys into source code, documentation examples, or commits. `QwenClient.generate_image()` provides text-to-image infrastructure support, but no image route is exposed yet.
