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
- `app/utils/`: reusable utility code, such as SMTP email sending.
- `frontend/`: static Vue + Element Plus frontend served by FastAPI.
- `tests/`: Python and frontend verification scripts.
- `scripts/`: database and presentation helper scripts.

## Run

```powershell
python main.py
```

The compatibility entrypoint still exposes `main:app`, so existing `uvicorn main:app --host 127.0.0.1 --port 8088` commands continue to work.

## Frontend

The frontend is a Vite application under `frontend/`.

Development:

```powershell
cd frontend
npm install
npm run dev -- --port 5173
```

The Vite dev server proxies backend API requests to `http://127.0.0.1:8088`.

Production build:

```powershell
cd frontend
npm run build
```

After build, FastAPI serves `frontend/dist/index.html` and static assets under `/frontend`. If `frontend/dist` does not exist, FastAPI falls back to the source `frontend/index.html`, which is intended for Vite development rather than direct browser use.

## API Response

Backend APIs return a unified structure:

```json
{
  "code": 1,
  "msg": "success",
  "data": null
}
```

## Runtime Logging

The backend uses `app/core/logger.py` and `app/core/logging_middleware.py` for developer runtime logs.

Default outputs:

- Console: all logs at the configured level.
- `logs/app.log`: application and request logs.
- `logs/error.log`: `ERROR` and `CRITICAL` logs only.

Useful environment variables:

- `LOG_LEVEL`: logging level, default `INFO`. Use `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
- `LOG_DIR`: log directory, default `logs`.
- `LOG_MAX_BYTES`: max size of each log file before rotation, default `10485760`.
- `LOG_BACKUP_COUNT`: number of rotated files to keep, default `5`.

The request logging middleware records method, path, filtered query string, status code, duration, and client IP. Sensitive query keys such as `password`, `token`, `authorization`, `secret`, and `api_key` are masked.

## Role Permissions

The backend uses role-based access plus service-layer data scope filtering.

Roles:

- `admin`: full access, including logs and permission-sensitive system modules.
- `teacher`: student, class, score, employment, statistics, and AI features; data is limited to linked teaching classes.
- `student`: personal profile, own scores, own employment data, and common AI features; data is limited to `users.student_id`.
- `consultant`: student and employment workflows for assigned students; data is limited by `students.consultant_id == users.teacher_id`.

The `users` table includes optional identity binding fields:

- `teacher_id`: links a login account to a teacher record.
- `student_id`: links a login account to a student record.

For existing databases without these fields, run:

```powershell
python scripts/ensure_user_identity_columns.py
```

Default development accounts are created on startup when missing:

- `admin` / `admin123`
- `teacher` / `teacher123`
- `consultant` / `consultant123`
- `student` / `student123`

The non-admin accounts are not bound to real teacher or student records by default. Set `users.teacher_id` and `users.student_id` to real IDs before validating scoped data access.

## AI Chat API

`POST /ai/chat` creates or continues an AI chat session. Request body:

```json
{
  "session_id": "optional-existing-session-id",
  "message": "你好"
}
```

The service stores user and assistant messages in `ai_chat_sessions` and `ai_chat_messages`, then uses the latest `AI_CHAT_CONTEXT_LIMIT` messages as context. Third-party model calls are handled by `app/core/qwen_client.py`, so controller and DAO code do not call DashScope directly.

AI chat also supports user-level long-term memory through `ai_chat_memories`. When a user explicitly says `记住...`, the backend stores that content as memory and injects the current user's active memories as a system message before calling the model. Long-term memory is separated by login user and works across different chat sessions.

Memory management APIs:

- `GET /ai/memories`: list the current user's active memories.
- `POST /ai/memories`: manually add one memory with `{"content": "..."}`.
- `DELETE /ai/memories/{memory_id}`: delete one memory owned by the current user.

Configure Qwen/DashScope with environment variables:

- `QWEN_API_KEY`: DashScope API Key. `DASHSCOPE_API_KEY` is also accepted for compatibility.
- `QWEN_TEXT_MODEL`: text chat model, default `qwen-plus`. `AI_CHAT_MODEL` is accepted as a compatibility fallback.
- `QWEN_IMAGE_MODEL`: image model, default `qwen-image-2.0-pro`.
- `QWEN_BASE_URL`: DashScope base URL, default `https://dashscope.aliyuncs.com/api/v1`.
- `QWEN_TIMEOUT_SECONDS`: request timeout, default `30`.
- `AI_CHAT_CONTEXT_LIMIT`: number of recent chat messages used as context, default `10`.
- `AI_CHAT_MEMORY_LIMIT`: number of long-term memories injected into chat context, default `10`.

Do not write real API Keys into source code, documentation examples, or commits. `QwenClient.generate_image()` provides text-to-image infrastructure support, but no image route is exposed yet.

## Local Letter And Email API

`POST /letters/generate` uses local Ollama to generate a Chinese letter. `POST /letters/send` generates the letter and sends it by SMTP.

Generate request:

```json
{
  "recipient": "assistant_teacher",
  "topic": "感谢老师最近的帮助",
  "method": "chat",
  "tone": "真诚、自然"
}
```

Send request adds email fields:

```json
{
  "recipient": "head_teacher",
  "topic": "请假说明",
  "method": "generate",
  "to_email": "teacher@example.com",
  "subject": "请假说明"
}
```

Configure Ollama and SMTP with environment variables:

- `OLLAMA_BASE_URL`: local Ollama base URL, default `http://localhost:11434`.
- `OLLAMA_MODEL`: local model name, default `llama3.1`.
- `OLLAMA_TIMEOUT_SECONDS`: request timeout, default `60`.
- `SMTP_HOST`: SMTP server host.
- `SMTP_PORT`: SMTP port, default `587`.
- `SMTP_USERNAME`: SMTP login username.
- `SMTP_PASSWORD`: SMTP password or authorization code.
- `SMTP_SENDER`: sender email address. Defaults to `SMTP_USERNAME` when omitted.
- `SMTP_USE_TLS`: whether to use STARTTLS, default `true`.

Install and start Ollama locally, then pull the configured model before calling these APIs. For example: `ollama pull llama3.1`.

## Weather API

`GET /weather/current?city=北京` queries current weather by city. `GET /weather/current?latitude=39.9042&longitude=116.4074` queries current weather by coordinates. `GET /weather/geocode?city=北京` queries city coordinates.

Configure Amap weather access with environment variables:

- `WEATHER_API_KEY`: Amap API key. `AMAP_API_KEY` is also accepted.
- `WEATHER_BASE_URL`: API base URL, default `https://restapi.amap.com`.
- `WEATHER_TIMEOUT_SECONDS`: request timeout, default `30`.
