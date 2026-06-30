"""用户认证路由（与原 NestJS /api/v1/user 路径对齐）"""
from __future__ import annotations

from fastapi import APIRouter, Request, UploadFile, File

from app.auth_schemas import (
    RefreshTokenRequest,
    UserLogin,
    UserRegister,
    UserUpdate,
)
from app.deps import CurrentUser, SessionDep
from app.schemas import error
from app.services.auth import get_me, login, refresh_token, register, update_user
from app.services.upload import upload_avatar

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/login")
async def user_login(body: UserLogin, db: SessionDep):
    """用户登录（phone + password）"""
    return await login(db, body)


@router.post("/register")
async def user_register(body: UserRegister, db: SessionDep):
    """用户注册"""
    return await register(db, body)


@router.post("/refresh-token")
async def user_refresh_token(body: RefreshTokenRequest, db: SessionDep):
    """刷新 access token"""
    return await refresh_token(db, body)


@router.post("/update-user")
async def user_update(
    body: UserUpdate,
    db: SessionDep,
    current_user: CurrentUser,
):
    """更新用户信息（需要鉴权）"""
    return await update_user(db, current_user["userId"], body)


@router.get("/me")
async def user_me(db: SessionDep, current_user: CurrentUser):
    """获取当前用户信息（需要鉴权）"""
    return await get_me(db, current_user["userId"])


@router.post("/upload-avatar")
async def user_upload_avatar(
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
):
    """上传头像到 MinIO（需要鉴权）"""
    return await upload_avatar(file, current_user["userId"])
