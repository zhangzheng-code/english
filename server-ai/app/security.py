"""JWT + 密码哈希工具"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import settings

# bcrypt 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    验证密码。
    兼容原 NestJS 的明文密码：如果 hashed 不是 bcrypt 格式，
    则退化为明文比对（迁移期间过渡用）。
    """
    if hashed.startswith("$2"):
        # bcrypt 哈希格式
        return pwd_context.verify(plain, hashed)
    # 明文兼容（原 NestJS 存的是明文）
    return plain == hashed


def create_token(data: dict, expires_delta: timedelta) -> str:
    """生成 JWT token"""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_access_token(user_id: str, name: str, email: str | None) -> str:
    """生成 access token（与原 NestJS payload 结构一致）"""
    return create_token(
        data={
            "userId": user_id,
            "name": name,
            "email": email,
            "tokenType": "access",
        },
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str, name: str, email: str | None) -> str:
    """生成 refresh token（7 天有效期）"""
    return create_token(
        data={
            "userId": user_id,
            "name": name,
            "email": email,
            "tokenType": "refresh",
        },
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict:
    """
    解码 JWT token。
    失败时抛出 jwt.InvalidTokenError 或 jwt.ExpiredSignatureError。
    """
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
