"""
Pydantic 数据模型 — 注册 / 登录 / Token 响应
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    username: str = Field(...)  # 允许用 username 或 email 登录
    password: str = Field(...)


class UserResponse(BaseModel):
    id: int
    uuid: str
    username: str
    email: str
    role: str
    is_active: bool
    email_verified: bool
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 60 * 24 * 7 * 60  # 秒


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserProfileResponse(BaseModel):
    user_id: int
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    subscription_plan: str = "free"
    video_quota: int = 3
    preferred_language: str = "zh-CN"
    preferred_voice: str = "zh-CN-XiaoxiaoNeural"
    preferred_video_ratio: str = "9:16"
