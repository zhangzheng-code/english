from __future__ import annotations

from datetime import datetime, timedelta

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, WordBookRecord


def create_query_tool(session: AsyncSession):
    @tool
    async def query_tool(userId: str) -> dict:
        """根据用户id查询用户学习的单词记录"""
        stmt = select(User).where(User.id == userId)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return {"error": "用户不存在"}

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        records_stmt = (
            select(WordBookRecord)
            .where(WordBookRecord.user_id == userId)
            .where(WordBookRecord.created_at >= today_start)
            .where(WordBookRecord.created_at < tomorrow_start)
        )
        records_result = await session.execute(records_stmt)
        records = records_result.scalars().all()

        return {
            "email": user.email,
            "name": user.name,
            "word_number": user.word_number,
            "today_words_count": len(records),
        }

    return query_tool


def create_search_tool(user_id: str, file_id: str | None = None):
    """
    创建一个绑定了 user_id 的专属文档检索工具。
    在执行搜索时，强制使用 metadata filter 隔离当前用户的知识文档。
    """
    from langchain_chroma import Chroma
    from app.llm.embeddings import get_embeddings
    from app.config import settings
    import os

    @tool
    async def search_user_corpus(query: str) -> str:
        """在用户已上传的专属资料库中检索特定的【知识或语义内容】。
        注意：入参 query 必须是用户想查询的【核心业务语义或问题描述】（例如 '工作经历'、'项目经验'），严禁直接传入文件名或书名号全称。"""
        if not os.path.exists(settings.chroma_db_dir):
            return "专属资料库为空，未找到相关文档内容。"

        try:
            embeddings = get_embeddings()
            vector_store = Chroma(
                collection_name="user_corpus",
                embedding_function=embeddings,
                persist_directory=settings.chroma_db_dir
            )

            results = []
            # 必须确保 file_id 100% 存在，严禁无书跨语料污染
            if file_id:
                where_filter = {
                    "$and": [
                        {"user_id": user_id},
                        {"file_id": str(file_id)}
                    ]
                }
                print(f"[DEBUG RAG] 收到工具调用! 用户输入的检索关键词 query='{query}'")
                print(f"[DEBUG RAG] 传递给 Chroma 的过滤条件 where_filter={where_filter}")
                results = vector_store.similarity_search(
                    query=query,
                    k=3,
                    filter=where_filter
                )
                print(f"[DEBUG RAG] Chroma 单书检索返回的文档数量: {len(results)}")
            else:
                # 无选中书籍时强制引导，严禁跨书污染
                return "请先在右侧精读书架中选中您要对练的特定英文材料，再发起提问。"

            if not results:
                return "没有检索到你上传的文件中包含该词汇的相关上下文。"

            formatted = []
            for doc in results:
                filename = doc.metadata.get("filename", "未知文件")
                page = doc.metadata.get("page", 0)
                page_str = f"第 {page} 页" if page else ""
                formatted.append(
                    f"【出自图书/资料：《{filename}》{page_str}】\n"
                    f"原文内容：{doc.page_content}\n"
                )

            return "\n---\n".join(formatted)
        except Exception as e:
            return f"检索失败: {str(e)}"

    return search_user_corpus


def create_oral_practice_tool(user_id: str):
    """
    创建一个绑定了 user_id 的口语陪练启动工具。
    当前端/大模型识别出特定的物理情境需要触发真实口语交互时调用。
    """
    @tool
    async def start_oral_practice(topic: str, role: str) -> str:
        """根据提供的主题（topic）和角色（role），向当前用户发起实时口语练习邀请并激活交互面板。
        例如：topic="Airport customs clearance", role="Customs Officer"
        """
        try:
            from app.socketio import sio
            # 广播邀请事件到该用户的专属 Room 中
            await sio.emit(
                "practiceInvitation",
                {"topic": topic, "role": role},
                room=f"user_{user_id}"
            )
            return f"已成功向客户端发送口语陪练邀请。主题：{topic}，角色扮演：{role}。"
        except Exception as e:
            return f"触发口语练习邀请失败: {str(e)}"

    return start_oral_practice


_mcp_tools_cache = None


async def get_translation_mcp_tools():
    """
    连接本地 translate_mcp_server.py MCP 服务，获取解析工具。
    """
    global _mcp_tools_cache
    import asyncio
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _mcp_tools_cache is not None and _mcp_tools_cache[0] is current_loop and current_loop is not None and not current_loop.is_closed():
        return _mcp_tools_cache[1]

    import sys
    from pathlib import Path
    from langchain_mcp_adapters.client import MultiServerMCPClient
    
    server_script = str(Path(__file__).resolve().parents[2] / "translate_mcp_server.py")
    
    client = MultiServerMCPClient({
        "english_parser": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [server_script]
        }
    })
    tools = await client.get_tools()
    _mcp_tools_cache = (current_loop, tools)
    return tools
