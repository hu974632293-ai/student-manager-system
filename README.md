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
