import pytest
import os
import shutil
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage

from app.services.chat import stream_chat
from app.config import settings

TEST_CHROMA_DIR = "./test_chroma_db_chat"

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # 设置测试的 chroma db 目录并创建它
    original_dir = settings.chroma_db_dir
    settings.chroma_db_dir = TEST_CHROMA_DIR
    os.makedirs(TEST_CHROMA_DIR, exist_ok=True)
    yield
    # 清理
    if os.path.exists(TEST_CHROMA_DIR):
        try:
            shutil.rmtree(TEST_CHROMA_DIR)
        except Exception:
            pass
    settings.chroma_db_dir = original_dir


@pytest.mark.asyncio
@patch("langchain_chroma.Chroma")
async def test_search_user_corpus_tool(mock_chroma):
    """测试无 file_id 时工具返回选书引导提示，严禁降级为全库搜索（防交叉污染）"""
    from app.llm.tools import create_search_tool
    
    user_id = "test_user_789"
    query = "Harry Potter"
    
    # Mock Chroma（不应被调用）
    mock_vectorstore = MagicMock()
    mock_chroma.return_value = mock_vectorstore
    
    # 创建不带 file_id 的搜索工具
    search_tool = create_search_tool(user_id)
    
    # 验证工具名称
    assert search_tool.name == "search_user_corpus"
    
    # 运行工具（无 file_id）
    result = await search_tool.ainvoke({"query": query})
    
    # 验证：应返回选书引导提示，而非执行检索
    assert "请先在右侧精读书架中选中" in result
    
    # 验证：similarity_search 严禁被调用（防止全库污染）
    mock_vectorstore.similarity_search.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.chat.create_deepseek")
@patch("app.services.chat.get_checkpoint")
@patch("langchain_chroma.Chroma")
async def test_stream_chat_with_rag_tool(mock_chroma, mock_checkpoint, mock_deepseek):
    """测试在聊天过程中注入 RAG 工具，且大模型能够成功调用它"""
    user_id = "test_user_789"
    
    # Mock Chroma
    mock_vectorstore = MagicMock()
    mock_doc = MagicMock()
    mock_doc.page_content = "Harry found the Snitch on page 12."
    mock_doc.metadata = {"filename": "HarryPotter.txt", "page": 12}
    mock_vectorstore.similarity_search.return_value = [mock_doc]
    mock_chroma.return_value = mock_vectorstore
    
    # Mock LLM and Agent
    mock_llm = MagicMock()
    mock_deepseek.return_value = mock_llm
    mock_checkpoint.return_value = None
    
    # Mock Agent Stream Events
    from langchain_core.messages import AIMessage
    mock_msg = AIMessage(content="根据你的专属图书《HarryPotter.txt》第 12 页，Harry found the Snitch.")
    
    async def mock_astream(*args, **kwargs):
        yield mock_msg
        
    mock_agent = MagicMock()
    mock_agent.astream = mock_astream
    
    # 拦截 build_agent
    with patch("app.services.chat.build_agent", return_value=mock_agent) as mock_build:
        body = {
            "role": "normal",
            "content": "Where did Harry find the Snitch?",
            "userId": user_id,
            "deepThink": False,
            "webSearch": False
        }
        
        events = []
        async for event in stream_chat(body):
            events.append(event)
            
        assert len(events) > 0
        assert events[0]["content"] == "根据你的专属图书《HarryPotter.txt》第 12 页，Harry found the Snitch."
        
        # 验证 build_agent 调用时是否传入了 tools 参数，且包含 search_user_corpus 工具
        mock_build.assert_called_once()
        passed_tools = mock_build.call_args[1].get("tools", [])
        assert any(t.name == "search_user_corpus" for t in passed_tools)


@pytest.mark.asyncio
@patch("langchain_chroma.Chroma")
async def test_search_user_corpus_tool_with_file_id(mock_chroma):
    """测试指定 file_id 时，使用 $and 操作符嵌套格式对 Chroma 进行多条件检索过滤"""
    from app.llm.tools import create_search_tool
    
    user_id = "test_user_789"
    file_id = "test_file_000"
    query = "magic wand"
    
    # Mock Chroma
    mock_vectorstore = MagicMock()
    mock_doc = MagicMock()
    mock_doc.page_content = "Harry got a new magic wand."
    mock_doc.metadata = {"filename": "wand.txt", "page": 1}
    mock_vectorstore.similarity_search.return_value = [mock_doc]
    mock_chroma.return_value = mock_vectorstore
    
    # 创建带有 file_id 的专属文档检索工具
    search_tool = create_search_tool(user_id, file_id)
    
    # 运行工具
    result = await search_tool.ainvoke({"query": query})
    
    # 验证是否使用了 $and 多条件过滤
    mock_chroma.assert_called_once()
    mock_vectorstore.similarity_search.assert_called_once_with(
        query=query,
        k=3,
        filter={
            "$and": [
                {"user_id": user_id},
                {"file_id": file_id}
            ]
        }
    )
    assert "wand.txt" in result
