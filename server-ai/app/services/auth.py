"""认证服务：登录、注册、刷新 token、更新用户"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_schemas import (
    LoginResponse,
    RefreshTokenRequest,
    TokenPair,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.db.models import User
from app.schemas import error, success
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

import jwt


def _user_to_response(user: User) -> dict:
    """将 User 模型转为响应字典（不含 password）"""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "address": user.address,
        "avatar": user.avatar,
        "bio": user.bio,
        "isTimingTask": user.is_timing_task,
        "timingTaskTime": user.timing_task_time,
        "wordNumber": user.word_number,
        "dayNumber": user.day_number,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "updatedAt": user.updated_at.isoformat() if user.updated_at else None,
        "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
    }


async def login(db: AsyncSession, body: UserLogin) -> dict:
    """用户登录"""
    stmt = select(User).where(User.phone == body.phone)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return error(message="手机号不存在")

    if not verify_password(body.password, user.password):
        return error(message="密码不正确")

    # 更新 lastLoginAt
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # 生成 token
    access_token = create_access_token(user.id, user.name, user.email)
    refresh_token = create_refresh_token(user.id, user.name, user.email)

    data = _user_to_response(user)
    data["token"] = {"accessToken": access_token, "refreshToken": refresh_token}
    return success(data)


async def register(db: AsyncSession, body: UserRegister) -> dict:
    """用户注册"""
    # 检查手机号是否已存在
    stmt = select(User).where(User.phone == body.phone)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        return error(message="手机号已经存在")

    # 检查邮箱是否已存在
    if body.email:
        stmt = select(User).where(User.email == body.email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            return error(message="邮箱已经存在")

    # 创建用户（密码使用 bcrypt 哈希）
    from cuid import cuid
    now = datetime.utcnow()
    user = User(
        id=cuid(),
        name=body.name,
        phone=body.phone,
        email=body.email,
        password=hash_password(body.password),
        last_login_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 生成 token
    access_token = create_access_token(user.id, user.name, user.email)
    refresh_token = create_refresh_token(user.id, user.name, user.email)

    data = _user_to_response(user)
    data["token"] = {"accessToken": access_token, "refreshToken": refresh_token}
    return success(data)


async def refresh_token(db: AsyncSession, body: RefreshTokenRequest) -> dict:
    """刷新 token"""
    try:
        payload = decode_token(body.refresh_token)
    except jwt.ExpiredSignatureError:
        return error(message="token已过期或无效", code=401)
    except jwt.InvalidTokenError:
        return error(message="token已过期或无效", code=401)

    if payload.get("tokenType") != "refresh":
        return error(message="token已过期或无效", code=401)

    # 查询用户确认存在
    stmt = select(User).where(User.id == payload["userId"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return error(message="用户不存在")

    # 生成新 token 对
    new_access = create_access_token(user.id, user.name, user.email)
    new_refresh = create_refresh_token(user.id, user.name, user.email)

    return success({"accessToken": new_access, "refreshToken": new_refresh})


async def update_user(db: AsyncSession, user_id: str, body: UserUpdate) -> dict:
    """更新用户信息"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return error(message="用户不存在")

    update_data = body.model_dump(exclude_unset=True)
    # 将驼峰字段名映射到蛇形模型字段
    field_map = {
        "is_timing_task": "is_timing_task",
        "timing_task_time": "timing_task_time",
    }
    for key, value in update_data.items():
        model_field = field_map.get(key, key)
        setattr(user, model_field, value)

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    return success(_user_to_response(user))


async def get_me(db: AsyncSession, user_id: str) -> dict:
    """获取当前用户信息"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return error(message="用户不存在")
    return success(_user_to_response(user))
