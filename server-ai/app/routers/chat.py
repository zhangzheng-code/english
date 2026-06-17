from __future__ import annotations

import json

from fastapi import APIRouter, Query
from fastapi.requests import Request
from sse_starlette.sse import EventSourceResponse

from app.services.chat import get_chat_history, stream_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(request: Request):
    body = await request.json()

    async def event_generator():
        async for chunk in stream_chat(body):
            # 必须 JSON 序列化，否则 sse-starlette 会用 str() 转成 Python dict 格式
            yield {"data": json.dumps(chunk, ensure_ascii=False)}

    return EventSourceResponse(event_generator())


@router.get("/history")
async def chat_history(userId: str = Query(...), role: str = Query(...)):
    return await get_chat_history(userId, role)
