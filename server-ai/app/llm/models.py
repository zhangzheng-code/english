from langchain_deepseek import ChatDeepSeek

from app.config import settings


def create_deepseek() -> ChatDeepSeek:
    return ChatDeepSeek(
        api_key=settings.deepseek_api_key,
        model=settings.deepseek_api_model,
        temperature=1.3,
        max_tokens=4396,
        streaming=True,
    )


def create_deepseek_reasoner() -> ChatDeepSeek:
    return ChatDeepSeek(
        api_key=settings.deepseek_api_key,
        model=settings.deepseek_reasoner_api_model,
        temperature=1.3,
        max_tokens=18000,
        streaming=True,
    )
