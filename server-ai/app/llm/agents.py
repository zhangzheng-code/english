from __future__ import annotations

from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import create_react_agent


def build_agent(
    model: ChatDeepSeek,
    system_prompt: str,
    checkpointer: AsyncPostgresSaver | None = None,
    tools: list | None = None,
):
    kwargs = {
        "model": model,
        "tools": tools or [],
        "prompt": system_prompt,
    }
    if checkpointer is not None:
        kwargs["checkpointer"] = checkpointer
    return create_react_agent(**kwargs)
