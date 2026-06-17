from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.llm.checkpoint import close_checkpoint, init_checkpoint
from app.routers import chat, digest, prompt
from app.tasks.digest import setup_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await init_checkpoint()
    setup_scheduler()
    yield
    # shutdown
    shutdown_scheduler()
    await close_checkpoint()


app = FastAPI(
    title="AI Service",
    lifespan=lifespan,
)

# 注册路由，前缀与原 NestJS 一致: /ai/v1
app.include_router(chat.router, prefix="/ai/v1")
app.include_router(prompt.router, prefix="/ai/v1")
app.include_router(digest.router, prefix="/ai/v1")


@app.get("/ai/v1/")
async def health():
    return {"message": "AI service is running"}
