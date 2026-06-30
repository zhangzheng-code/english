import pytest
import os
import shutil
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.config import settings

# 确保测试环境的临时上传目录被设置且干净
TEST_TEMP_DIR = "/tmp/test_chunks"
settings.temp_upload_dir = TEST_TEMP_DIR

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # 测试前清理
    if os.path.exists(TEST_TEMP_DIR):
        shutil.rmtree(TEST_TEMP_DIR)
    os.makedirs(TEST_TEMP_DIR, exist_ok=True)
    yield
    # 测试后清理
    if os.path.exists(TEST_TEMP_DIR):
        shutil.rmtree(TEST_TEMP_DIR)


def test_upload_check_not_found():
    """测试查询未上传过的 MD5"""
    from app.deps import get_current_user, get_session
    app.dependency_overrides[get_current_user] = lambda: {"userId": "test_user_id", "name": "test_user"}
    
    # Mock DB 返回 None (表示文件不存在)
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    app.dependency_overrides[get_session] = lambda: mock_db
    
    with TestClient(app) as client:
        response = client.get("/ai/v1/upload/check?md5=nonexistentmd5")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["exists"] is False
        assert data["data"]["uploadedChunks"] == []

    app.dependency_overrides.clear()


def test_upload_chunk():
    """测试上传分片"""
    from app.deps import get_current_user, get_session
    app.dependency_overrides[get_current_user] = lambda: {"userId": "test_user_id", "name": "test_user"}

    # 虽然 chunk 上传不需要 db，但 app 初始化依赖 db，需要 mock get_session 避免连接真实 DB
    mock_db = AsyncMock()
    app.dependency_overrides[get_session] = lambda: mock_db

    with TestClient(app) as client:
        md5_val = "testfilemd512345"
        # 上传第 0 个分片
        response = client.post(
            "/ai/v1/upload/chunk",
            data={
                "md5": md5_val,
                "chunkIndex": 0,
                "totalChunks": 2
            },
            files={"file": ("chunk_0", b"Hello ", "application/octet-stream")}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 上传第 1 个分片
        response = client.post(
            "/ai/v1/upload/chunk",
            data={
                "md5": md5_val,
                "chunkIndex": 1,
                "totalChunks": 2
            },
            files={"file": ("chunk_1", b"World!", "application/octet-stream")}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 再次 check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        response = client.get(f"/ai/v1/upload/check?md5={md5_val}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["exists"] is False
        assert set(data["data"]["uploadedChunks"]) == {0, 1}

    app.dependency_overrides.clear()


@patch("app.services.upload._get_minio_client")
def test_upload_merge(mock_get_minio):
    """测试合并分片并持久化"""
    from app.deps import get_current_user, get_session
    app.dependency_overrides[get_current_user] = lambda: {"userId": "test_user_id", "name": "test_user"}

    # Mock MinIO 客户端
    mock_minio = MagicMock()
    mock_minio.bucket_exists.return_value = True
    mock_get_minio.return_value = mock_minio

    # Mock 数据库 Session
    mock_db = AsyncMock()
    app.dependency_overrides[get_session] = lambda: mock_db

    md5_val = "testfilemd512345"
    chunk_dir = os.path.join(TEST_TEMP_DIR, md5_val)
    os.makedirs(chunk_dir, exist_ok=True)
    with open(os.path.join(chunk_dir, "0"), "wb") as f:
        f.write(b"Hello ")
    with open(os.path.join(chunk_dir, "1"), "wb") as f:
        f.write(b"World!")

    with TestClient(app) as client:
        response = client.post(
            "/ai/v1/upload/merge",
            json={
                "md5": md5_val,
                "filename": "hello_world.txt",
                "totalChunks": 2,
                "size": 12
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "fileId" in data["data"]
        assert "url" in data["data"]
        
        # 验证 MinIO put_object 被正确调用
        mock_minio.put_object.assert_called_once()
        # 验证 DB add & commit 写入成功
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("app.services.upload._get_minio_client")
@patch("langchain_chroma.Chroma")
async def test_upload_delete(mock_chroma, mock_get_minio):
    """测试专属电子书的删除逻辑，包含 MinIO 与 Chroma 的清理"""
    from app.db.models import UserFile
    from app.deps import get_current_user, get_session
    import tempfile
    import shutil
    
    # 设置并创建测试临时 Chroma 目录，确保 os.path.exists 校验为真
    original_chroma_dir = settings.chroma_db_dir
    test_chroma_dir = tempfile.mkdtemp()
    settings.chroma_db_dir = test_chroma_dir
    
    try:
        mock_minio = MagicMock()
        mock_get_minio.return_value = mock_minio
        
        # Mock Chroma
        mock_vectorstore = MagicMock()
        mock_chroma.return_value = mock_vectorstore
        
        # Mock Current User
        app.dependency_overrides[get_current_user] = lambda: {
            "userId": "test_user_123",
            "email": "test@example.com"
        }
        
        # Mock DB Session
        mock_db = AsyncMock()
        mock_file = UserFile(
            id="test_file_999",
            user_id="test_user_123",
            filename="dummy.txt",
            md5="dummymd5",
            size=100,
            url="/minio/user-corpus/dummy.txt"
        )
        
        # Mock execute return value for querying UserFile
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_file
        mock_db.execute.return_value = mock_result
        
        app.dependency_overrides[get_session] = lambda: mock_db
        
        with TestClient(app) as client:
            response = client.delete("/ai/v1/upload/test_file_999")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "删除成功"
            
            # 验证 MinIO delete 被正确调用
            mock_minio.remove_object.assert_called_once_with("user-corpus", "dummy.txt")
            # 验证 Chroma delete 被正确调用
            mock_vectorstore._collection.delete.assert_called_once_with(where={"file_id": "test_file_999"})
            # 验证 DB delete & commit 被正确调用
            mock_db.delete.assert_called_once_with(mock_file)
            mock_db.commit.assert_called_once()
            
        app.dependency_overrides.clear()
    finally:
        shutil.rmtree(test_chroma_dir, ignore_errors=True)
        settings.chroma_db_dir = original_chroma_dir
