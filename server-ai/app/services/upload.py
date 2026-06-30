"""MinIO 文件上传服务"""
from __future__ import annotations

import os
import uuid
from datetime import timedelta

from fastapi import UploadFile
from minio import Minio

from app.config import settings
from app.schemas import error, success


def _get_minio_client() -> Minio:
    """创建 MinIO 客户端"""
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


async def upload_avatar(file: UploadFile, user_id: str) -> dict:
    """
    上传头像到 MinIO：
    1. 验证文件类型
    2. 生成唯一文件名
    3. 上传到 MinIO
    4. 返回 previewUrl 和 databaseUrl
    """
    # 验证文件类型
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        return error(message="只支持 JPG、PNG、GIF、WEBP 格式的图片")

    # 验证文件大小（最大 5MB）
    file_size = 0
    file_data = await file.read()
    file_size = len(file_data)
    if file_size > 5 * 1024 * 1024:
        return error(message="图片大小不能超过 5MB")

    # 生成唯一文件名
    ext = file.filename.split(".")[-1] if file.filename else "jpg"
    object_name = f"avatars/{user_id}/{uuid.uuid4().hex}.{ext}"

    try:
        client = _get_minio_client()

        # 确保 bucket 存在
        if not client.bucket_exists(settings.minio_bucket):
            client.make_bucket(settings.minio_bucket)

        # 上传文件
        from io import BytesIO
        client.put_object(
            settings.minio_bucket,
            object_name,
            BytesIO(file_data),
            length=file_size,
            content_type=file.content_type,
        )

        # 生成预览 URL（7 天有效）
        preview_url = client.presigned_get_object(
            settings.minio_bucket,
            object_name,
            expires=timedelta(days=7),
        )

        # databaseUrl 是相对路径，存储在数据库中
        database_url = f"/minio/{settings.minio_bucket}/{object_name}"

        return success({
            "previewUrl": preview_url,
            "databaseUrl": database_url,
        })

    except Exception as e:
        return error(message=f"上传失败: {str(e)}")


async def check_upload_status(db: AsyncSession, md5: str, user_id: str) -> dict:
    """检查分片上传状态（支持秒传和断点续传查询）"""
    from sqlalchemy import select
    from app.db.models import UserFile

    # 1. 检查文件是否已完全上传（秒传）
    stmt = select(UserFile).where(UserFile.md5 == md5)
    result = await db.execute(stmt)
    user_file = result.scalar_one_or_none()
    if user_file:
        return success({
            "exists": True,
            "uploadedChunks": [],
            "file": {
                "fileId": user_file.id,
                "url": user_file.url,
                "filename": user_file.filename
            }
        })

    # 2. 检查本地已上传的分片索引
    chunk_dir = os.path.join(settings.temp_upload_dir, md5)
    uploaded_chunks = []
    if os.path.exists(chunk_dir):
        for name in os.listdir(chunk_dir):
            if name.isdigit():
                uploaded_chunks.append(int(name))

    return success({
        "exists": False,
        "uploadedChunks": sorted(uploaded_chunks)
    })


async def save_upload_chunk(file: UploadFile, md5: str, chunk_index: int, total_chunks: int) -> dict:
    """保存分片文件到本地临时暂存目录"""
    import os
    try:
        chunk_dir = os.path.join(settings.temp_upload_dir, md5)
        os.makedirs(chunk_dir, exist_ok=True)
        chunk_path = os.path.join(chunk_dir, str(chunk_index))

        content = await file.read()
        with open(chunk_path, "wb") as f:
            f.write(content)

        return success({"message": f"分片 {chunk_index} 上传成功"})
    except Exception as e:
        return error(message=f"保存分片失败: {str(e)}")


async def register_file_fast(
    db: AsyncSession,
    md5: str,
    filename: str,
    total_chunks: int,
    size: int,
    user_id: str
) -> dict:
    """
    【快速登记】：仅做前置校验 + DB 写入 processing 状态，1 秒内立即返回 file_id。
    物理合并和向量化由调用方通过 BackgroundTasks 离线完成。
    """
    import os
    from cuid import cuid
    from app.db.models import UserFile

    chunk_dir = os.path.join(settings.temp_upload_dir, md5)
    if not os.path.exists(chunk_dir):
        return error(message="分片目录不存在")

    uploaded_chunks = [int(name) for name in os.listdir(chunk_dir) if name.isdigit()]
    if len(uploaded_chunks) < total_chunks:
        return error(message=f"分片文件不完整，当前 {len(uploaded_chunks)}/{total_chunks}")

    # 预生成稳定 file_id 和存储路径（后台任务使用相同路径）
    ext = filename.split(".")[-1] if "." in filename else "bin"
    file_id = cuid()
    bucket_name = "user-corpus"
    object_name = f"user_files/{user_id}/{file_id}.{ext}"
    database_url = f"/minio/{bucket_name}/{object_name}"

    # 仅写入 DB 元数据，状态为 processing
    user_file = UserFile(
        id=file_id,
        user_id=user_id,
        filename=filename,
        md5=md5,
        size=size,
        url=database_url,
        status="processing"
    )
    db.add(user_file)
    await db.commit()

    return success({
        "fileId": file_id,
        "url": database_url,
        "filename": filename
    })


def sync_merge_and_upload(md5: str, total_chunks: int, object_name: str, bucket_name: str) -> None:
    """
    【后台同步链条】：物理合并分片 + 上传 MinIO，在线程池中执行（无事件循环依赖）。
    完成后删除本地临时文件。
    """
    import os
    import shutil

    chunk_dir = os.path.join(settings.temp_upload_dir, md5)
    merged_file_path = os.path.join(settings.temp_upload_dir, f"{md5}_merged")

    try:
        os.makedirs(settings.temp_upload_dir, exist_ok=True)
        with open(merged_file_path, "wb") as outfile:
            for i in range(total_chunks):
                chunk_file = os.path.join(chunk_dir, str(i))
                if not os.path.exists(chunk_file):
                    raise FileNotFoundError(f"缺失分片 {i}")
                with open(chunk_file, "rb") as infile:
                    outfile.write(infile.read())

        merged_size = os.path.getsize(merged_file_path)
        client = _get_minio_client()
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

        with open(merged_file_path, "rb") as merged_file:
            client.put_object(
                bucket_name,
                object_name,
                merged_file,
                length=merged_size,
                content_type="application/octet-stream"
            )

        shutil.rmtree(chunk_dir, ignore_errors=True)
        os.remove(merged_file_path)
        print(f"[MERGE] 物理合并+MinIO上传完成: {object_name}")

    except Exception as e:
        print(f"[MERGE ERROR] 合并或上传失败: {e}")
        if os.path.exists(merged_file_path):
            os.remove(merged_file_path)
        raise

