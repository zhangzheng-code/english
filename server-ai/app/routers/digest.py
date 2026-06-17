from __future__ import annotations

import asyncio

from fastapi import APIRouter

from app.schemas import success
from app.services.digest import handle_daily_digest

router = APIRouter(prefix="/digest", tags=["digest"])


@router.post("/trigger")
async def trigger_digest():
    """手动触发每日摘要任务（测试用）"""
    asyncio.create_task(handle_daily_digest())
    return success({"message": "摘要任务已触发，请查看服务端日志"})
