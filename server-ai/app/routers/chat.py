from __future__ import annotations

import json

from fastapi import APIRouter, Query
from fastapi.requests import Request
from sse_starlette.sse import EventSourceResponse

from app.llm.context import set_model_type, set_image_url
from app.services.chat import get_chat_history, stream_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(request: Request):
    body = await request.json()
    
    # 绑定当前请求的模型参数与图片URL到协程上下文
    model_type = "reasoner" if body.get("deepThink", False) else "flash"
    image_url = body.get("imageUrl")
    set_model_type(model_type)
    set_image_url(image_url)

    async def event_generator():
        # 确保在异步生成器子协程中也正确注入
        set_model_type(model_type)
        set_image_url(image_url)
        try:
            async for chunk in stream_chat(body):
                # 必须 JSON 序列化，否则 sse-starlette 会用 str() 转成 Python dict 格式
                yield {"data": json.dumps(chunk, ensure_ascii=False)}
        except Exception as e:
            err_chunk = {"content": f"\n[请求处理遇到异常: {str(e)}]", "role": "ai", "type": "chat"}
            yield {"data": json.dumps(err_chunk, ensure_ascii=False)}

    return EventSourceResponse(event_generator())


@router.get("/history")
async def chat_history(userId: str = Query(...), role: str = Query(...)):
    return await get_chat_history(userId, role)
