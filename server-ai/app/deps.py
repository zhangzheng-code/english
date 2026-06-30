"""FastAPI 依赖注入"""
from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.security import decode_token

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# HTTP Bearer scheme（自动从 Authorization: Bearer <token> 提取 token）
_bearer = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> dict:
    """
    鉴权依赖：解析 JWT access token，返回 payload。
    用法：
        @router.get("/protected")
        async def protected(user = Depends(get_current_user)):
            return {"userId": user["userId"]}
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token已过期或无效",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token已过期或无效",
        )

    if payload.get("tokenType") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token已过期或无效",
        )

    return payload


CurrentUser = Annotated[dict, Depends(get_current_user)]
