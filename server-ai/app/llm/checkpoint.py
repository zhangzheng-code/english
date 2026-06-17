from __future__ import annotations

import asyncio
import logging
import selectors
import sys

from app.config import settings

logger = logging.getLogger(__name__)

_checkpointer = None
_ctx_manager = None
_is_memory = False


def _ensure_selector_loop():
    """Windows: 确保当前事件循环是 SelectorEventLoop（psycopg 要求）"""
    if sys.platform != "win32":
        return
    try:
        loop = asyncio.get_running_loop()
        if not isinstance(loop, asyncio.SelectorEventLoop):
            logger.warning("当前事件循环不是 SelectorEventLoop，psycopg 可能不可用")
    except RuntimeError:
        # 没有运行中的事件循环，设置策略即可
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def init_checkpoint():
    """初始化 checkpointer：优先 PostgresSaver，失败则降级 MemorySaver"""
    global _checkpointer, _ctx_manager, _is_memory

    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        _ctx_manager = AsyncPostgresSaver.from_conn_string(settings.langchain_database_url)
        _checkpointer = await _ctx_manager.__aenter__()
        await _checkpointer.setup()
        _is_memory = False
        logger.info("PostgresSaver checkpoint initialized (persistent)")
    except Exception as e:
        logger.warning(f"PostgresSaver failed ({e}), falling back to MemorySaver")
        from langgraph.checkpoint.memory import MemorySaver
        _checkpointer = MemorySaver()
        _is_memory = True


async def close_checkpoint():
    """关闭连接"""
    global _checkpointer, _ctx_manager, _is_memory
    if _ctx_manager is not None:
        try:
            await _ctx_manager.__aexit__(None, None, None)
        except Exception:
            pass
    _ctx_manager = None
    _checkpointer = None
    _is_memory = False


def get_checkpoint():
    """获取 checkpointer 实例"""
    if _checkpointer is None:
        raise RuntimeError("Checkpoint not initialized")
    return _checkpointer


def is_memory_checkpoint() -> bool:
    """是否使用内存 checkpointer（无持久化）"""
    return _is_memory
