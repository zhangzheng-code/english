from typing import Any
from langchain.agents import create_agent
from app.llm.middleware import dynamic_model_selector


def build_agent(
    model: Any,
    system_prompt: str,
    checkpointer: Any = None,
    tools: list | None = None,
):
    kwargs = {
        "model": model,
        "tools": tools or [],
        "system_prompt": system_prompt,
        "middleware": [dynamic_model_selector],
    }
    if checkpointer is not None:
        kwargs["checkpointer"] = checkpointer
    return create_agent(**kwargs)
