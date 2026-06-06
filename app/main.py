from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.controllers.ai_chat import ai_chat_router
from app.controllers.auth import auth_router, ensure_default_users
from app.controllers.classes import class_router
from app.controllers.data_query import data_query_router
from app.controllers.jobs import router_job
from app.controllers.letter import letter_router
from app.controllers.logs import logs_router
from app.controllers.score import router_score
from app.controllers.statistics import statistics_router
from app.controllers.student import students_router
from app.controllers.teacher import teacher_router
from app.controllers.weather import weather_router
from app.core.logger import get_logger
from app.core.logging_middleware import RequestLoggingMiddleware
from app.core.response import fail
from app.core.schema_compat import ensure_ai_chat_schema_compat


logger = get_logger("app")

FRONTEND_ROOT = Path("frontend")
FRONTEND_DIST = FRONTEND_ROOT / "dist"
FRONTEND_STATIC_DIR = FRONTEND_DIST if FRONTEND_DIST.exists() else FRONTEND_ROOT
FRONTEND_INDEX = FRONTEND_STATIC_DIR / "index.html"

VALIDATION_MESSAGE_MAP = {
    "missing": "为必填项",
    "int_parsing": "必须是整数",
    "float_parsing": "必须是数字",
    "bool_parsing": "必须是布尔值",
    "date_from_datetime_parsing": "必须是有效日期",
    "date_from_datetime_inexact": "必须是有效日期",
    "string_too_short": "长度过短",
    "string_too_long": "长度过长",
    "greater_than": "必须大于指定值",
    "greater_than_equal": "必须大于或等于指定值",
    "less_than": "必须小于指定值",
    "less_than_equal": "必须小于或等于指定值",
}

FIELD_LABEL_MAP = {
    "username": "账号",
    "password": "密码",
    "page": "页码",
    "size": "每页条数",
    "limit": "条数",
    "student_id": "学号",
    "student_name": "学生姓名",
    "class_id": "班级",
    "teacher_id": "教师",
    "exam_round": "考试轮次",
    "score": "分数",
    "salary": "薪资",
    "city": "城市",
    "latitude": "纬度",
    "longitude": "经度",
    "question": "问题",
    "message": "消息内容",
    "content": "正文",
    "subject": "主题",
    "to_email": "收件邮箱",
}


def _format_validation_errors(errors: list[dict]) -> list[dict]:
    formatted = []
    for error in errors:
        loc = error.get("loc") or []
        field = ".".join(str(item) for item in loc if item not in {"body", "query", "path"})
        label = FIELD_LABEL_MAP.get(field, field or "请求参数")
        message = VALIDATION_MESSAGE_MAP.get(str(error.get("type")), "参数格式不正确")
        formatted.append(
            {
                "field": field or "请求参数",
                "msg": f"{label}{message}",
            }
        )
    return formatted

app = FastAPI(title="学生管理系统", description="FastAPI + Vue3 学生管理后台")
app.add_middleware(RequestLoggingMiddleware)

app.include_router(ai_chat_router)
app.include_router(letter_router)
app.include_router(logs_router)
app.include_router(auth_router)
app.include_router(weather_router)
app.include_router(data_query_router)
app.include_router(statistics_router)
app.include_router(teacher_router)
app.include_router(router_job)
app.include_router(students_router)
app.include_router(router_score)
app.include_router(class_router)
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_STATIC_DIR)), name="frontend")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTP异常 path=%s status=%s detail=%s", request.url.path, exc.status_code, exc.detail)
    return JSONResponse(status_code=exc.status_code, content=fail(str(exc.detail)))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("请求参数校验失败 path=%s errors=%s", request.url.path, exc.errors())
    return JSONResponse(status_code=422, content=fail("request validation failed", _format_validation_errors(exc.errors())))


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("数据库异常 path=%s", request.url.path)
    return JSONResponse(status_code=500, content=fail("database error"))


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.exception("服务异常 path=%s", request.url.path)
    return JSONResponse(status_code=500, content=fail("server error"))


@app.on_event("startup")
def startup():
    logger.info("学生管理系统后端启动")
    ensure_default_users()
    ensure_ai_chat_schema_compat()


@app.get("/", summary="打开前端首页")
async def root():
    return FileResponse(FRONTEND_INDEX)


@app.get("/admin", summary="打开管理后台页面")
async def admin_page():
    return FileResponse(FRONTEND_INDEX)


@app.get("/dashboard", summary="打开数据看板页面")
async def dashboard_page():
    return FileResponse(FRONTEND_INDEX)


@app.get("/{frontend_path:path}", summary="打开前端路由页面")
async def frontend_page(frontend_path: str):
    frontend_routes = {
        "login",
        "profile",
        "students",
        "classes",
        "teachers",
        "scores",
        "employment",
        "statistics",
        "letters",
        "weather",
        "geocode",
        "logs",
        "ai-chat",
        "data-query",
        "permissions",
        "forbidden",
    }
    if frontend_path in frontend_routes:
        return FileResponse(FRONTEND_INDEX)
    raise HTTPException(status_code=404, detail="not found")
