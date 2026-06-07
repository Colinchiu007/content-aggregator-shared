"""
认证路由 — 注册 / 登录 / 刷新 Token / 查询当前用户
依赖 shared/auth/jwt_handler.py 和 shared/auth/models.py
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from psycopg2.extras import DictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from shared.auth.jwt_handler import create_access_token, create_refresh_token, get_user_from_token
from shared.auth.models import (
    PasswordReset,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserLogin,
    UserProfileResponse,
    UserRegister,
    UserResponse,
)

# ---------------------------------------------------------------------------
# 配置 — 生产环境请通过环境变量或配置文件注入
# ---------------------------------------------------------------------------
DATABASE_URL: str = (
    "postgresql://postgres:postgres@127.0.0.1:5432/user_db"
)
JWT_SECRET: str = "dev-secret-key-change-in-production!"

# FastAPI 不自动暴露以下路由的文档（可选）
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()


# ---------------------------------------------------------------------------
# 数据库辅助
# ---------------------------------------------------------------------------
def _get_conn():
    """获取 psycopg2 连接（用于简单查询）。"""
    import psycopg2
    return psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        password="postgres",
        dbname="user_db",
    )


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister):
    """
    用户注册。
    成功时自动创建 users + user_profiles 两条记录。
    """
    conn = _get_conn()
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # 重名 / 重邮箱检查
            cur.execute(
                "SELECT id FROM users WHERE username=%s OR email=%s;",
                (body.username, body.email),
            )
            if cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="用户名或邮箱已被注册",
                )

            pwd_hash = _hash_password(body.password)
            now = datetime.now(tz=timezone.utc)
            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, uuid, username, email, role, is_active, email_verified, created_at;
                """,
                (body.username, body.email, pwd_hash, now, now),
            )
            row = cur.fetchone()

            # 同时创建 user_profiles 默认行
            cur.execute(
                """
                INSERT INTO user_profiles (user_id, created_at, updated_at)
                VALUES (%s, %s, %s);
                """,
                (row["id"], now, now),
            )
            conn.commit()

            return UserResponse(
                id=row["id"],
                uuid=str(row["uuid"]),
                username=row["username"],
                email=row["email"],
                role=row["role"],
                is_active=row["is_active"],
                email_verified=row["email_verified"],
                created_at=str(row["created_at"]),
            )
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"注册失败: {e}") from e
    finally:
        conn.close()


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin):
    """
    用户登录（支持 username 或 email）。
    返回 access_token + refresh_token。
    """
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # 兼容 username 或 email 登录
            cur.execute(
                """
                SELECT id, uuid, username, email, password_hash, role, is_active
                FROM users
                WHERE username=%s OR email=%s;
                """,
                (body.username, body.username),
            )
            row = cur.fetchone()
            if not row or not _verify_password(body.password, row["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误",
                )
            if not row["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="账号已被禁用",
                )

            # 更新最后登录时间
            now = datetime.now(tz=timezone.utc)
            cur.execute(
                "UPDATE users SET last_login=%s, updated_at=%s WHERE id=%s;",
                (now, now, row["id"]),
            )
            conn.commit()

            access_token = create_access_token(
                user_id=row["id"],
                username=row["username"],
                role=row["role"],
            )
            refresh_token = create_refresh_token(user_id=row["id"])

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
            )
    finally:
        conn.close()


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest):
    """
    用 refresh_token 换取新的 access_token。
    """
    user_info = get_user_from_token(body.refresh_token)
    if not user_info or user_info.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 refresh token",
        )

    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                "SELECT username, role FROM users WHERE id=%s AND is_active=TRUE;",
                (user_info["user_id"],),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="用户不存在或已禁用")
            new_access = create_access_token(
                user_id=user_info["user_id"],
                username=row["username"],
                role=row["role"],
            )
            new_refresh = create_refresh_token(user_id=user_info["user_id"])
            return TokenResponse(access_token=new_access, refresh_token=new_refresh)
    finally:
        conn.close()


@router.get("/me", response_model=UserProfileResponse)
def get_me(cred: HTTPAuthorizationCredentials = Depends(security)):
    """
    获取当前登录用户的信息（需要 Bearer Token）。
    """
    user_info = get_user_from_token(cred.credentials)
    if not user_info:
        raise HTTPException(status_code=401, detail="未登录或 token 已过期")

    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                """
                SELECT u.id, u.username, u.email, u.role,
                       p.display_name, p.avatar_url, p.bio, p.website,
                       p.company, p.location, p.subscription_plan,
                       p.video_quota, p.preferred_language,
                       p.preferred_voice, p.preferred_video_ratio
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE u.id=%s AND u.is_active=TRUE;
                """,
                (user_info["user_id"],),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="用户不存在或已禁用")

            return UserProfileResponse(
                user_id=row["id"],
                username=row["username"],
                display_name=row["display_name"],
                avatar_url=row["avatar_url"],
                bio=row["bio"],
                website=row["website"],
                company=row["company"],
                location=row["location"],
                subscription_plan=row["subscription_plan"] or "free",
                video_quota=row["video_quota"] or 3,
                preferred_language=row["preferred_language"] or "zh-CN",
                preferred_voice=row["preferred_voice"] or "zh-CN-XiaoxiaoNeural",
                preferred_video_ratio=row["preferred_video_ratio"] or "9:16",
            )
    finally:
        conn.close()
