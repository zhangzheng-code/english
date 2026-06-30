import os
import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import settings
from app.llm.embeddings import get_embeddings
from app.db.models import UserFile

logger = logging.getLogger(__name__)


async def vectorize_text(
    db: AsyncSession,
    user_id: str,
    file_id: str,
    filename: str,
    text_content: str
) -> dict:
    """
    语义切块并写入 Chroma 隔离空间：
    1. 使用 LangChain SemanticChunker 切分长文本为语义块
    2. 对每个块打上隔离元数据 (user_id, file_id)
    3. 利用 Chroma 将分块批量持久化写入本地向量库
    """
    try:
        embeddings = get_embeddings()

        # RecursiveCharacterTextSplitter: 零 Embedding 调用，处理 79MB 文本约 1-2 秒
        # chunk_size=800 字符 ≈ 150-200 token，overlap=100 保留上下文衔接
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )
        chunks = await asyncio.to_thread(text_splitter.split_text, text_content)

        documents = []
        for idx, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "user_id": user_id,
                    "file_id": file_id,
                    "filename": filename,
                    "chunk_index": idx
                }
            )
            documents.append(doc)

        # 确保持久化目录存在
        os.makedirs(settings.chroma_db_dir, exist_ok=True)

        # 挂载或载入 Chroma
        vector_store = Chroma(
            collection_name="user_corpus",
            embedding_function=embeddings,
            persist_directory=settings.chroma_db_dir
        )

        # 批量写入分块 (每 100 个文档一组进行 Batch 刷入)
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            await asyncio.to_thread(vector_store.add_documents, batch)
            logger.info(f"Vectorize: Written batch {i // batch_size + 1}/{-(-len(documents) // batch_size)} for file_id={file_id}")

        logger.info(f"Vectorize: Successfully processed {len(chunks)} chunks for file_id={file_id}")

        return {
            "success": True,
            "chunks_count": len(chunks),
            "message": f"成功切分为 {len(chunks)} 个语义块并存入向量库"
        }

    except Exception as e:
        logger.error(f"Vectorize: Failed to vectorize text for file_id={file_id}: {e}")
        return {
            "success": False,
            "chunks_count": 0,
            "message": f"向量化失败: {str(e)}"
        }


async def vectorize_file_task(db: AsyncSession, user_file_id: str) -> dict:
    """
    异步文件提取与向量化主任务：
    1. 从 Postgres 查询文件元数据
    2. 从 MinIO 获取二进制流，解析为纯文本
    3. 调用 vectorize_text 进行向量写入
    4. 更新 UserFile 状态为 completed / failed
    """
    from app.services.upload import _get_minio_client

    # 1. 查询元数据
    stmt = select(UserFile).where(UserFile.id == user_file_id)
    result = await db.execute(stmt)
    user_file = result.scalar_one_or_none()
    if not user_file:
        logger.error(f"Vectorize Task: UserFile {user_file_id} not found")
        return {"success": False, "message": "文件元数据未找到"}

    try:
        # 2. 从 MinIO 读取内容
        minio_client = _get_minio_client()
        # url 存储格式为 "/minio/{bucket}/{object_name}"
        # 提取 bucket_name 与 object_name (动态支持任意存储桶)
        bucket_name = settings.minio_bucket
        object_name = user_file.url
        if user_file.url.startswith("/minio/"):
            parts = user_file.url.split("/", 3)
            if len(parts) >= 4:
                bucket_name = parts[2]
                object_name = parts[3]

        response = minio_client.get_object(bucket_name, object_name)
        file_bytes = response.read()
        response.close()

        # 3. 提取纯文本内容 (默认尝试 UTF-8 编码，对 txt 文件完美适用)
        # 如果是 PDF/Word，可在此处扩展专业库解析
        text_content = ""
        filename_lower = user_file.filename.lower()
        if filename_lower.endswith(".pdf"):
            try:
                import pypdf
                from io import BytesIO
                
                def extract_pdf_sync(data):
                    stream = BytesIO(data)
                    reader = pypdf.PdfReader(stream)
                    text = "\n\n".join([page.extract_text() or "" for page in reader.pages])
                    try:
                        stream.close()
                    except Exception:
                        pass
                    return text

                import asyncio
                text_content = await asyncio.to_thread(extract_pdf_sync, file_bytes)
                
                # 显式内存释放，强制进行垃圾收集回收大文件字节流
                import gc
                gc.collect()
            except ImportError:
                # 缺失 pypdf 时的极简兼容降级
                text_content = file_bytes.decode("utf-8", errors="ignore")
        else:
            text_content = file_bytes.decode("utf-8", errors="ignore")

        # 4. 执行向量化
        res = await vectorize_text(
            db=db,
            user_id=user_file.user_id,
            file_id=user_file.id,
            filename=user_file.filename,
            text_content=text_content
        )

        # 5. 更新状态
        user_file.status = "completed" if res["success"] else "failed"
        await db.commit()

        return res

    except Exception as e:
        logger.error(f"Vectorize Task: Task failed for file {user_file_id}: {e}")
        try:
            await db.rollback()
            user_file.status = "failed"
            await db.commit()
        except Exception as commit_err:
            logger.error(f"Vectorize Task: Failed to mark file as failed: {commit_err}")
        return {"success": False, "message": f"执行失败: {str(e)}"}
