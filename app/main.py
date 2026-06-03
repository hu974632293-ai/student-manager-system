from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.controllers.ai_chat import ai_chat_router
from app.controllers.auth import auth_router, ensure_default_users
from app.controllers.classes import class_router
from app.controllers.jobs import router_job
from app.controllers.letter import letter_router
from app.controllers.score import router_score
from app.controllers.statistics import statistics_router
from app.controllers.student import students_router
from app.controllers.teacher import teacher_router
from app.controllers.weather import weather_router
from app.core.response import fail


app = FastAPI(title="学生管理系统", description="FastAPI + Vue3 学生管理后台")

app.include_router(ai_chat_router)
app.include_router(letter_router)
app.include_router(auth_router)
app.include_router(weather_router)
app.include_router(statistics_router)
app.include_router(teacher_router)
app.include_router(router_job)
app.include_router(students_router)
app.include_router(router_score)
app.include_router(class_router)
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=fail(str(exc.detail)))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content=fail("request validation failed", exc.errors()))


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=500, content=fail("database error"))


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content=fail("server error"))


@app.on_event("startup")
def startup():
    ensure_default_users()


@app.get("/", summary="打开前端首页")
async def root():
    return FileResponse("frontend/index.html")


@app.get("/admin", summary="打开管理后台页面")
async def admin_page():
    return FileResponse("frontend/index.html")


@app.get("/dashboard", summary="打开数据看板页面")
async def dashboard_page():
    return FileResponse("frontend/index.html")
