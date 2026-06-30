from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.llm.checkpoint import close_checkpoint, init_checkpoint
from app.routers import auth, chat, digest, pay, prompt, upload, recommend
from app.socketio import sio
from app.tasks.digest import setup_scheduler, shutdown_scheduler


# ---- 应用生命周期 ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    # 自动创建本地未初始化的 SQLModel 数据库表（仅在非测试环境下执行）
    import os
    import sys
    if "pytest" not in sys.modules and "PYTEST_CURRENT_TEST" not in os.environ:
        from app.db.engine import engine
        from sqlmodel import SQLModel
        from app.db import models
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    await init_checkpoint()
    setup_scheduler()
    yield
    # shutdown
    shutdown_scheduler()
    await close_checkpoint()


app = FastAPI(
    title="English App - FastAPI",
    lifespan=lifespan,
)


# ---- 全局异常处理器（与原 NestJS exceptionFilter 对齐）----

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic 校验失败 → 422 重写为标准格式"""
    errors = exc.errors()
    msgs = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msgs.append(f"{loc}: {err.get('msg', '')}")
    message = "参数校验失败: " + "; ".join(msgs) if msgs else "参数校验失败"
    return JSONResponse(
        status_code=200,
        content={"data": None, "code": 400, "message": message, "success": False},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """FastAPI HTTP 异常 → 标准格式"""
    return JSONResponse(
        status_code=200,
        content={"data": None, "code": exc.status_code, "message": str(exc.detail), "success": False},
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Starlette HTTP 异常（404 等）→ 标准格式"""
    return JSONResponse(
        status_code=200,
        content={"data": None, "code": exc.status_code, "message": str(exc.detail), "success": False},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """未知异常 → 500 标准格式"""
    return JSONResponse(
        status_code=200,
        content={"data": None, "code": 500, "message": "服务器内部错误", "success": False},
    )


# ---- 注册路由 ----
# AI 微服务: /ai/v1
app.include_router(chat.router, prefix="/ai/v1")
app.include_router(prompt.router, prefix="/ai/v1")
app.include_router(digest.router, prefix="/ai/v1")
# 用户认证: /api/v1/user
app.include_router(auth.router, prefix="/api/v1")
# 支付: /api/v1/pay
app.include_router(pay.router, prefix="/api/v1")
# 文件上传: /ai/v1/upload
app.include_router(upload.router, prefix="/ai/v1")
# 课程推荐: /ai/v1/recommend
app.include_router(recommend.router, prefix="/ai/v1")


@app.get("/ai/v1/")
async def health():
    return {"message": "AI service is running"}


# ---- Socket.IO ASGI 挂载（与 FastAPI 共享端口）----
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
