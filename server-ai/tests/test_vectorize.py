import pytest
import os
import shutil
from unittest.mock import AsyncMock, MagicMock, patch
from app.config import settings

# 设置测试环境中的 Chroma DB 目录
TEST_CHROMA_DIR = "./test_chroma_db"
settings.chroma_db_dir = TEST_CHROMA_DIR

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # 清理已存在的测试 Chroma DB
    if os.path.exists(TEST_CHROMA_DIR):
        try:
            shutil.rmtree(TEST_CHROMA_DIR)
        except Exception:
            pass
    yield
    # 回收垃圾以解除 sqlite/Chroma 文件占用
    import gc
    gc.collect()
    if os.path.exists(TEST_CHROMA_DIR):
        try:
            shutil.rmtree(TEST_CHROMA_DIR)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_semantic_chunking_and_vectorization():
    """测试长文本语义切片并写入 Chroma 隔离空间"""
    from app.tasks.vectorize import vectorize_text
    
    user_id = "test_user_123"
    file_id = "test_file_456"
    filename = "ielts_reading.txt"
    
    # 构建测试长文本（>800 字符），确保 RecursiveCharacterTextSplitter 能切出 ≥2 块
    long_text = (
        "English is a West Germanic language that was first spoken in early medieval England. "
        "It is named after the Angles, one of the ancient Germanic peoples that migrated to the area of Great Britain. "
        "English has developed over the course of more than 1,400 years. "
        "The earliest forms of English, a group of West Germanic dialects brought to Great Britain by Anglo-Saxon settlers in the 5th century, "
        "are collectively called Old English. Middle English began in the late 11th century with the Norman conquest of England. "
        "Early Modern English began in the late 15th century with the introduction of the printing press to London. "
        "\n\n"
        "Artificial intelligence is intelligence demonstrated by machines, as opposed to natural intelligence displayed by animals. "
        "AI applications include advanced web search engines, recommendation systems, understanding human speech, "
        "self-driving cars, generative or creative tools, and automated decision-making. "
        "Machine learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed. "
        "Deep learning uses neural networks with many layers to analyze various factors of data. "
        "Natural language processing allows computers to understand and generate human language. "
        "Computer vision enables machines to interpret and understand visual information from the world. "
        "Reinforcement learning trains AI agents to make sequences of decisions to maximize rewards."
    )
    
    # 模拟 DB session
    mock_db = AsyncMock()
    
    # 运行向量化异步函数
    result = await vectorize_text(
        db=mock_db,
        user_id=user_id,
        file_id=file_id,
        filename=filename,
        text_content=long_text
    )
    
    assert result["success"] is True
    assert result["chunks_count"] >= 2
    
    # 从 ChromaDB 中检索，验证用户级隔离
    from app.llm.embeddings import get_embeddings
    from langchain_chroma import Chroma
    
    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name="user_corpus",
        embedding_function=embeddings,
        persist_directory=TEST_CHROMA_DIR
    )
    
    # 验证检索过滤 (仅检索当前 user_id)
    search_results = vector_store.similarity_search(
        query="Germanic language",
        k=2,
        filter={"user_id": user_id}
    )
    
    assert len(search_results) > 0
    assert any("medieval England" in doc.page_content for doc in search_results)
    
    # 验证元数据是否正确存入
    for doc in search_results:
        assert doc.metadata["user_id"] == user_id
        assert doc.metadata["file_id"] == file_id
        assert doc.metadata["filename"] == filename
        assert "chunk_index" in doc.metadata
