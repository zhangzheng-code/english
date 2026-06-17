from __future__ import annotations

from typing import AsyncIterator

import httpx
from langchain_core.messages import HumanMessage

from app.config import settings
from app.llm.agents import build_agent
from app.llm.checkpoint import get_checkpoint
from app.llm.models import create_deepseek, create_deepseek_reasoner
from app.schemas import success

# 聊天人格 system prompt（与原 NestJS prompt.mode.ts 完全一致）
ROLE_PROMPTS = {
    "normal": "你是一个女仆请根据用户的对话内容，给出相应的回答，请用中文回答",
    "master": "你是一个英语大师，这是一个英语学习的对话，根据用户的对话内容，给出相应的回答(使用专业术语)，请用英文回答",
    "business": "你是一个商务英语专家，这是一个商务英语的对话，根据用户的对话内容，给出相应的回答(使用商务英语专业术语)，请用中文回答",
    "qilinge": "你是一个喜欢装逼，天马行空，说话不着边际的一个人，容易暴怒，请根据用户的对话内容，给出相应的回答(使用麒麟哥的语气)，需要一点发癫，发疯，并且你从不道歉，请用中文回答",
    "xiaoman": "你是一个知名程序员，这是一个程序员学习的对话，根据用户的对话内容，给出相应的回答(使用程序员专业术语)，请用中文回答",
}


async def bocha_search(query: str, count: int = 10) -> str:
    """调用博查搜索 API 获取联网搜索结果"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            settings.bocha_search_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.bocha_api_key}",
            },
            json={"query": query, "count": count, "summary": True},
            timeout=30.0,
        )
        data = resp.json()
        values = data.get("data", {}).get("webPages", {}).get("value", [])
        parts = []
        for item in values:
            parts.append(
                f"标题：{item.get('name', '')}\n"
                f"链接：{item.get('url', '')}\n"
                f"摘要：{item.get('summary', '').replace(chr(10), '')}\n"
                f"网站名称：{item.get('siteName', '')}\n"
                f"发布时间：{item.get('dateLastCrawled', '')}"
            )
        return "\n".join(parts)


async def stream_chat(body: dict) -> AsyncIterator[dict]:
    """
    SSE 流式聊天，产出 {content, role, type} 字典。
    前端通过 fetch-event-source 接收 data: {...} 格式。
    """
    role = body["role"]
    content = body["content"]
    deep_think = body.get("deepThink", False)
    web_search = body.get("webSearch", False)
    user_id = body["userId"]

    system_prompt = ROLE_PROMPTS.get(role)
    if not system_prompt:
        yield {"content": "模式不存在", "role": "ai", "type": "chat"}
        return

    # 联网搜索增强
    if web_search:
        search_results = await bocha_search(content)
        system_prompt += f"请根据以下搜索结果回答问题：{search_results}(并且返回你参考的网站名称)，用户问题：{content}"

    # 选择模型
    model = create_deepseek_reasoner() if deep_think else create_deepseek()

    # 获取 checkpointer
    checkpointer = get_checkpoint()

    # 构建 agent
    agent = build_agent(
        model=model,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
    )

    # 流式输出
    thread_id = f"{user_id}-{role}"
    async for event in agent.astream(
        {"messages": [HumanMessage(content=content)]},
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="messages",
    ):
        msg = event[0] if isinstance(event, tuple) else event

        # 深度思考内容
        reasoning = getattr(msg, "additional_kwargs", {}).get("reasoning_content", "")
        if reasoning:
            yield {"content": reasoning, "role": "ai", "type": "reasoning"}

        # 普通对话内容
        text = getattr(msg, "content", "")
        if text:
            yield {"content": text, "role": "ai", "type": "chat"}


async def get_chat_history(userId: str, role: str) -> dict:
    """查询聊天历史记录"""
    checkpointer = get_checkpoint()
    if checkpointer is None:
        return success([])
    thread_id = f"{userId}-{role}"
    checkpoint = await checkpointer.aget({"configurable": {"thread_id": thread_id}})

    if not checkpoint:
        return success([])

    messages = checkpoint.get("channel_values", {}).get("messages", [])
    result = []
    for msg in messages:
        item = {
            "content": getattr(msg, "content", ""),
            "role": getattr(msg, "type", "ai"),
        }
        reasoning = getattr(msg, "additional_kwargs", {}).get("reasoning_content", "")
        if reasoning:
            item["reasoning"] = reasoning
        result.append(item)

    return success(result)
