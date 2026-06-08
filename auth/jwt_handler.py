"""
JWT Token 处理模块
提供 JWT 生成、验证、解析工具函数。
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from jwt.algorithms import get_default_algorithms

# 配置从 shared.auth.config 动态加载
from shared.auth.config import get_config

_config = get_config()
JWT_SECRET_KEY: str = _config.JWT_SECRET_KEY
JWT_ALGORITHM: str = _config.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES: int = _config.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS: int = _config.REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(
    user_id: int,
    username: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """生成 JWT Access Token"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(tz=timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(
    user_id: int,
    expires_days: Optional[int] = None,
) -> str:
    """生成 JWT Refresh Token"""
    if expires_days is None:
        expires_days = get_config().REFRESH_TOKEN_EXPIRE_DAYS

    now = datetime.now(tz=timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=expires_days),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    解码并验证 JWT Token。
    失败时直接抛出 jwt 异常，由调用方捕获处理。
    """
    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={"require": ["exp", "sub"]},
    )


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    从 Token 中提取用户信息。
    返回值示例：
        {"user_id": 1, "username": "alice", "role": "user", "type": "access"}
    """
    try:
        payload = decode_token(token)
        return {
            "user_id": int(payload["sub"]),
            "username": payload.get("username", ""),
            "role": payload.get("role", "user"),
            "type": payload.get("type", "access"),
        }
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
        return None
