"""认证相关 Pydantic Schema（与原 NestJS DTO 对齐）"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---- 请求 Schema ----

class UserLogin(BaseModel):
    """登录请求：phone + password"""
    phone: str
    password: str


class UserRegister(BaseModel):
    """注册请求：name + phone + optional email + password"""
    name: str
    phone: str
    email: Optional[str] = None
    password: str


class RefreshTokenRequest(BaseModel):
    """刷新 token 请求"""
    refresh_token: str = Field(alias="refreshToken")

    model_config = {"populate_by_name": True}


class UserUpdate(BaseModel):
    """更新用户信息"""
    name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    is_timing_task: Optional[bool] = Field(default=None, alias="isTimingTask")
    timing_task_time: Optional[str] = Field(default=None, alias="timingTaskTime")

    model_config = {"populate_by_name": True}


# ---- 响应 Schema ----

class TokenPair(BaseModel):
    """JWT token 对"""
    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")

    model_config = {"populate_by_name": True}


class UserResponse(BaseModel):
    """用户信息响应（不含 password，与原 userSelect 对齐）"""
    id: str
    name: str
    email: Optional[str] = None
    phone: str
    address: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    is_timing_task: bool = Field(alias="isTimingTask")
    timing_task_time: str = Field(alias="timingTaskTime")
    word_number: int = Field(alias="wordNumber")
    day_number: int = Field(alias="dayNumber")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    last_login_at: Optional[datetime] = Field(default=None, alias="lastLoginAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class LoginResponse(BaseModel):
    """登录/注册响应：用户信息 + token 对"""
    id: str
    name: str
    email: Optional[str] = None
    phone: str
    address: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    is_timing_task: bool = Field(alias="isTimingTask")
    timing_task_time: str = Field(alias="timingTaskTime")
    word_number: int = Field(alias="wordNumber")
    day_number: int = Field(alias="dayNumber")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    last_login_at: Optional[datetime] = Field(default=None, alias="lastLoginAt")
    token: TokenPair

    model_config = {"from_attributes": True, "populate_by_name": True}


class TokenPayload(BaseModel):
    """JWT 解码后的 payload"""
    user_id: str = Field(alias="userId")
    name: str
    email: Optional[str] = None
    token_type: str = Field(alias="tokenType")

    model_config = {"populate_by_name": True}
