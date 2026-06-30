from fastapi import APIRouter, Depends, Form, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from app.deps import CurrentUser, SessionDep
from app.services.upload import check_upload_status, save_upload_chunk, register_file_fast, sync_merge_and_upload

router = APIRouter(prefix="/upload", tags=["upload"])


async def run_vectorize_background(file_id: str, md5: str, total_chunks: int, object_name: str, bucket_name: str):
    """
    【真·双轨后台链条】：
    1. asyncio.to_thread 物理合并分片并上传 MinIO
    2. 对接向量化任务
    """
    import asyncio
    from app.db.engine import async_session
    from app.tasks.vectorize import vectorize_file_task

    try:
        # Step 1: 线程池离线执行物理合并 + MinIO 上传
        await asyncio.to_thread(sync_merge_and_upload, md5, total_chunks, object_name, bucket_name)
    except Exception as e:
        # 合并失败：更新 DB 状态为 failed
        from app.db.engine import async_session
        from sqlalchemy import select
        from app.db.models import UserFile
        async with async_session() as db:
            result = await db.execute(select(UserFile).where(UserFile.id == file_id))
            user_file = result.scalar_one_or_none()
            if user_file:
                user_file.status = "failed"
                await db.commit()
        print(f"[BACKGROUND] 合并失败 file_id={file_id}: {e}")
        return

    # Step 2: 向量化
    async with async_session() as db:
        await vectorize_file_task(db, file_id)


class MergeRequest(BaseModel):
    md5: str
    filename: str
    totalChunks: int
    size: int


@router.get("/check")
async def check_upload(md5: str, current_user: CurrentUser, db: SessionDep):
    """
    检查分片上传状态：
    1. 是否已经秒传（检查数据库中是否存在该文件，若有则返回 exists=True）
    2. 若未完成上传，检查本地临时文件夹已上传了哪些分片块，返回分片索引列表
    """
    return await check_upload_status(db, md5, current_user["userId"])


@router.post("/chunk")
async def upload_chunk(
    md5: str = Form(...),
    chunkIndex: int = Form(...),
    totalChunks: int = Form(...),
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
):
    """
    上传单个分片：
    保存分片到本地临时文件夹 {temp_upload_dir}/{md5}/{chunkIndex}
    """
    return await save_upload_chunk(file, md5, chunkIndex, totalChunks)


@router.post("/merge")
async def merge_upload(
    body: MergeRequest,
    db: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """
    【秒级释放】合并接口：
    1. 仅做分片完整性校验 + DB 写入 processing，1 秒内向前端返回成功。
    2. 物理文件合并、MinIO 上传、向量化全路在 BackgroundTasks 离线完成。
    """
    ext = body.filename.split(".")[-1] if "." in body.filename else "bin"
    bucket_name = "user-corpus"

    res = await register_file_fast(
        db,
        body.md5,
        body.filename,
        body.totalChunks,
        body.size,
        current_user["userId"]
    )
    if res.get("success") and "fileId" in res.get("data", {}):
        file_id = res["data"]["fileId"]
        object_name = f"user_files/{current_user['userId']}/{file_id}.{ext}"
        background_tasks.add_task(
            run_vectorize_background,
            file_id, body.md5, body.totalChunks, object_name, bucket_name
        )
    return res


@router.get("/list")
async def list_files(current_user: CurrentUser, db: SessionDep):
    """
    获取当前用户专属精读书架的电子书列表
    """
    from sqlalchemy import select
    from app.db.models import UserFile

    stmt = (
        select(UserFile)
        .where(UserFile.user_id == current_user["userId"])
        .order_by(UserFile.created_at.desc())
    )
    result = await db.execute(stmt)
    files = result.scalars().all()
    return {
        "code": 200,
        "success": True,
        "data": [
            {
                "id": f.id,
                "filename": f.filename,
                "size": f.size,
                "md5": f.md5,
                "url": f.url,
                "status": f.status,
                "createdAt": f.created_at.isoformat() if f.created_at else None
            }
            for f in files
        ]
    }


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: CurrentUser,
    db: SessionDep,
):
    """
    删除指定的电子书：
    1. 校验文件所有权
    2. 从 MinIO 删除存储文件
    3. 从 Chroma 向量库中清除关联的向量切片
    4. 从 PostgreSQL 数据库中删除元数据记录
    """
    from sqlalchemy import select
    from app.db.models import UserFile
    from app.services.upload import _get_minio_client
    from langchain_chroma import Chroma
    from app.llm.embeddings import get_embeddings
    from app.config import settings
    import os

    # 1. 查询元数据
    stmt = select(UserFile).where(UserFile.id == file_id, UserFile.user_id == current_user["userId"])
    result = await db.execute(stmt)
    user_file = result.scalar_one_or_none()
    if not user_file:
        return {"code": 404, "success": False, "message": "未找到该文件或无权删除"}

    # 2. 从 MinIO 删除物理文件
    try:
        minio_client = _get_minio_client()
        parts = [p for p in user_file.url.split("/") if p]
        if len(parts) >= 3 and parts[0] == "minio":
            bucket = parts[1]
            object_name = "/".join(parts[2:])
            minio_client.remove_object(bucket, object_name)
    except Exception as e:
        print(f"[DELETE FILE] MinIO 删除失败: {e}")

    # 3. 从 Chroma 向量库中删除所有相关切片
    try:
        if os.path.exists(settings.chroma_db_dir):
            embeddings = get_embeddings()
            vector_store = Chroma(
                collection_name="user_corpus",
                embedding_function=embeddings,
                persist_directory=settings.chroma_db_dir
            )
            vector_store._collection.delete(where={"file_id": file_id})
            print(f"[DELETE FILE] Chroma 成功清除 file_id={file_id} 的切片")
    except Exception as e:
        print(f"[DELETE FILE] Chroma 删除失败: {e}")

    # 4. 从数据库中删除记录
    await db.delete(user_file)
    await db.commit()

    return {"code": 200, "success": True, "message": "删除成功"}

