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
    file_id = body.get("fileId") or body.get("file_id")

    system_prompt = ROLE_PROMPTS.get(role)
    if not system_prompt:
        yield {"content": "模式不存在", "role": "ai", "type": "chat"}
        return

    # 联网搜索增强
    if web_search:
        search_results = await bocha_search(content)
        system_prompt += f"请根据以下搜索结果回答问题：{search_results}(并且返回你参考的网站名称)，用户问题：{content}"

    # 专属资料库 RAG 提示词增强
    system_prompt += (
        "\n你拥有访问用户专属资料库的能力。如果用户提到或问及与其上传的文档、电子书或资料相关的内容，"
        "或者你需要为某个单词提供例句，你应该主动调用 `search_user_corpus` 工具检索上下文。"
        "如果通过检索找到了匹配的内容，你必须在回答中精准标出：‘此词/此句出自你上传的《{书名}》第 {页码} 页，原句是...’。"
    )

    from app.llm.context import set_model_type

    # 绑定模型类别到当前协程上下文，物理模型选择逻辑交给 wrap_model_call 中间件处理
    set_model_type("reasoner" if deep_think else "flash")
    model = create_deepseek()

    # 获取 checkpointer
    checkpointer = get_checkpoint()

    # 创建用户的专属 RAG 检索工具与翻译解析 MCP 工具
    from app.llm.tools import create_search_tool, get_translation_mcp_tools
    search_tool = create_search_tool(user_id, file_id)
    
    try:
        mcp_tools = await get_translation_mcp_tools()
    except Exception as e:
        import sys
        print(f"[WARN] 加载翻译 MCP 工具失败，将仅使用基础检索: {e}", file=sys.stderr)
        mcp_tools = []

    # 提示词增强：指引 AI 人格优先使用 MCP 工具
    system_prompt += (
        "\n当你需要帮用户翻译长句、解析生词、拆解语法或提供造句时，"
        "请主动调用 `smart_english_parser` 工具获取精细化的结构化数据，"
        "并结合你的人格设定（如女仆、英语大师、麒麟哥等）生动呈现给用户！"
    )

    # 构建 agent
    agent = build_agent(
        model=model,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        tools=[search_tool] + mcp_tools,
    )

    # 流式输出
    thread_id = f"{user_id}-{role}"
    image_url = body.get("imageUrl")
    add_kwargs = {"image_url": image_url} if image_url else {}
    from langchain_core.messages import AIMessage, AIMessageChunk

    async for event in agent.astream(
        {"messages": [HumanMessage(content=content, additional_kwargs=add_kwargs)]},
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="messages",
    ):
        msg = event[0] if isinstance(event, tuple) else event

        if not isinstance(msg, (AIMessage, AIMessageChunk)):
            continue

        # 深度思考内容
        reasoning = getattr(msg, "additional_kwargs", {}).get("reasoning_content", "")
        if reasoning:
            yield {"content": reasoning, "role": "ai", "type": "reasoning"}

        # 普通对话内容
        text = getattr(msg, "content", "")
        if isinstance(text, list):
            text = "".join([
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in text
                if isinstance(item, str) or (isinstance(item, dict) and item.get("type") == "text")
            ])
        elif not isinstance(text, str):
            text = str(text) if text else ""

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
        img_url = getattr(msg, "additional_kwargs", {}).get("image_url", "")
        if img_url:
            item["imageUrl"] = img_url
        result.append(item)

    return success(result)
