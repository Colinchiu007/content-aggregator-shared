"""
认证路由 — 注册 / 登录 / 刷新 Token / 查询当前用户

支持 PostgreSQL 和 SQLite 两种数据库后端。
依赖 shared/auth/jwt_handler.py 和 shared/auth/models.py
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from content_aggregator_shared.shared.auth.config import get_config, get_db_connection, get_pwd_context
from content_aggregator_shared.shared.auth.jwt_handler import create_access_token, create_refresh_token, get_user_from_token
from content_aggregator_shared.shared.auth.models import (
    PasswordReset,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserLogin,
    UserProfileResponse,
    UserRegister,
    UserResponse,
)
import secrets
from datetime import timedelta

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


# ---------------------------------------------------------------------------
# 数据库辅助
# ---------------------------------------------------------------------------
def _get_conn():
    """获取数据库连接（根据配置自动选择 PostgreSQL 或 SQLite）。"""
    return get_db_connection()


def _hash_password(password: str) -> str:
    return get_pwd_context().hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return get_pwd_context().verify(plain, hashed)


def _execute_with_cursor(conn, sql: str, params: tuple = ()):
    """执行 SQL，自动处理 PostgreSQL/SQLite 的游标差异。"""
    config = get_config()
    cur = conn.cursor()
    try:
        if config.DATABASE_TYPE == "postgresql":
            from psycopg2.extras import DictCursor
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute(sql, params)
        else:
            # SQLite
            cur.execute(sql, params)
            # SQLite 的 fetchone 返回 tuple，需要转换为 dict-like
            if sql.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cur.description]
                row = cur.fetchone()
                return dict(zip(columns, row)) if row else None
        return cur.fetchone()
    finally:
        cur.close()


def _execute_update(conn, sql: str, params: tuple = ()):
    """执行 UPDATE/INSERT，返回影响行数。"""
    config = get_config()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        if config.DATABASE_TYPE == "postgresql":
            conn.commit()
            return cur.rowcount
        else:
            conn.commit()
            return cur.rowcount
    finally:
        cur.close()


def _wrap_pg_dict(result) -> Dict:
    """将 PostgreSQL DictCursor 结果转为普通 dict（SQLite 不需要）。"""
    if result is None:
        return None
    if isinstance(result, dict):
        return result
    # 如果是 sqlite3.Row，也有 .keys() 方法
    if hasattr(result, "keys"):
        return {k: result[k] for k in result.keys()}
    return dict(result)


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
    try:
        if get_config().DATABASE_TYPE == "postgresql":
            conn.autocommit = False
            return _register_postgresql(conn, body)
        else:
            return _register_sqlite(conn, body)
    except HTTPException:
        raise
    except Exception as e:
        if get_config().DATABASE_TYPE == "postgresql":
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"注册失败: {e}") from e
    finally:
        conn.close()


def _register_postgresql(conn, body: UserRegister) -> UserResponse:
    from psycopg2.extras import DictCursor

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
        row = _wrap_pg_dict(cur.fetchone())

        # 同时创建 user_profiles 默认行
        cur.execute(
            "INSERT INTO user_profiles (user_id, created_at, updated_at) VALUES (%s, %s, %s);",
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


def _register_sqlite(conn, body: UserRegister) -> UserResponse:
    import uuid

    # 重名 / 重邮箱检查
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM users WHERE username=? OR email=?",
        (body.username, body.email),
    )
    if cur.fetchone():
        cur.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名或邮箱已被注册",
        )
    cur.close()

    pwd_hash = _hash_password(body.password)
    now = datetime.now(tz=timezone.utc).isoformat()
    user_uuid = str(uuid.uuid4())

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (username, email, password_hash, uuid, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (body.username, body.email, pwd_hash, user_uuid, now, now),
    )
    user_id = cur.lastrowid
    cur.close()

    # 同时创建 user_profiles 默认行
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_profiles (user_id, created_at, updated_at) VALUES (?, ?, ?)",
        (user_id, now, now),
    )
    cur.close()
    conn.commit()

    return UserResponse(
        id=user_id,
        uuid=user_uuid,
        username=body.username,
        email=body.email,
        role="user",
        is_active=True,
        email_verified=False,
        created_at=now,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin):
    """
    用户登录（支持 username 或 email）。
    返回 access_token + refresh_token。
    """
    conn = _get_conn()
    try:
        if get_config().DATABASE_TYPE == "postgresql":
            return _login_postgresql(conn, body)
        else:
            return _login_sqlite(conn, body)
    finally:
        conn.close()


def _login_postgresql(conn, body: UserLogin) -> TokenResponse:
    from psycopg2.extras import DictCursor

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
        row = _wrap_pg_dict(cur.fetchone())
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

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def _login_sqlite(conn, body: UserLogin) -> TokenResponse:
    cur = conn.cursor()
    # 兼容 username 或 email 登录
    cur.execute(
        """
        SELECT id, uuid, username, email, password_hash, role, is_active
        FROM users
        WHERE username=? OR email=?;
        """,
        (body.username, body.username),
    )
    row = cur.fetchone()
    if row:
        row = dict(zip([d[0] for d in cur.description], row))
    if not row or not _verify_password(body.password, row["password_hash"]):
        cur.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not row["is_active"]:
        cur.close()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    # 更新最后登录时间
    now = datetime.now(tz=timezone.utc).isoformat()
    cur.execute(
        "UPDATE users SET last_login=?, updated_at=? WHERE id=?",
        (now, now, row["id"]),
    )
    conn.commit()
    cur.close()

    access_token = create_access_token(
        user_id=row["id"],
        username=row["username"],
        role=row["role"],
    )
    refresh_token = create_refresh_token(user_id=row["id"])

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


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
        cur = conn.cursor()
        if get_config().DATABASE_TYPE == "postgresql":
            cur.execute(
                "SELECT username, role FROM users WHERE id=%s AND is_active=TRUE;",
                (user_info["user_id"],),
            )
        else:
            cur.execute(
                "SELECT username, role FROM users WHERE id=? AND is_active=TRUE;",
                (user_info["user_id"],),
            )
        row = cur.fetchone()
        if row:
            if get_config().DATABASE_TYPE == "postgresql":
                row = _wrap_pg_dict(row)
            else:
                row = dict(zip([d[0] for d in cur.description], row))
        cur.close()

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
        cur = conn.cursor()
        if get_config().DATABASE_TYPE == "postgresql":
            from psycopg2.extras import DictCursor
            cur = conn.cursor(cursor_factory=DictCursor)
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
            row = _wrap_pg_dict(cur.fetchone())
        else:
            cur.execute(
                """
                SELECT u.id, u.username, u.email, u.role,
                       p.display_name, p.avatar_url, p.bio, p.website,
                       p.company, p.location
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE u.id=? AND u.is_active=TRUE;
                """,
                (user_info["user_id"],),
            )
            row = cur.fetchone()
            if row:
                row = dict(zip([d[0] for d in cur.description], row))

        cur.close()

        if not row:
            raise HTTPException(status_code=401, detail="用户不存在或已禁用")

        return UserProfileResponse(
            user_id=row["id"],
            username=row["username"],
            display_name=row.get("display_name"),
            avatar_url=row.get("avatar_url"),
            bio=row.get("bio"),
            website=row.get("website"),
            company=row.get("company"),
            location=row.get("location"),
            subscription_plan=row.get("subscription_plan") or "free",
            video_quota=row.get("video_quota") or 3,
            preferred_language=row.get("preferred_language") or "zh-CN",
            preferred_voice=row.get("preferred_voice") or "zh-CN-XiaoxiaoNeural",
            preferred_video_ratio=row.get("preferred_video_ratio") or "9:16",
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 密码找回
# ---------------------------------------------------------------------------
@router.post("/forgot-password", status_code=200)
def forgot_password(body: PasswordResetRequest):
    """
    密码找回：输入注册邮箱，生成重置 token。
    由于未配置 SMTP，重置链接将直接返回在响应中（仅用于自托管环境）。
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        if get_config().DATABASE_TYPE == "postgresql":
            from psycopg2.extras import DictCursor
            cur_fetch = conn.cursor(cursor_factory=DictCursor)
            cur_fetch.execute("SELECT id, username, email FROM users WHERE email=%s AND is_active=TRUE;", (body.email,))
            row = _wrap_pg_dict(cur_fetch.fetchone())
            cur_fetch.close()
        else:
            cur.execute("SELECT id, username, email FROM users WHERE email=? AND is_active=TRUE;", (body.email,))
            row = cur.fetchone()
            if row:
                row = dict(zip([d[0] for d in cur.description], row))

        # 即使用户不存在也返回成功（防止邮箱枚举）
        if not row:
            cur.close()
            return {"message": "您输入的邮箱和用户信息不匹配，请重新输入。", "email_registered": False}

        # 生成重置 token（URL 安全，32 字节 = 43 字符）
        token = secrets.token_urlsafe(32)
        expires = (datetime.now(tz=timezone.utc) + timedelta(hours=1)).isoformat()

        # 存入数据库
        if get_config().DATABASE_TYPE == "postgresql":
            cur.execute("UPDATE users SET password_reset_token=%s, password_reset_token_expires=%s WHERE id=%s;", (token, expires, row["id"]))
        else:
            cur.execute("UPDATE users SET password_reset_token=?, password_reset_token_expires=? WHERE id=?;", (token, expires, row["id"]))
        conn.commit()
        cur.close()

        return {
            "message": "密码重置链接已生成",
            "reset_link": f"/auth/reset?token={token}",
            "token": token,
            "expires_in_hours": 1,
            "note": "请访问重置链接并输入新密码。链接1小时内有效。",
            "email_registered": True
        }
    finally:
        conn.close()


@router.post("/reset-password", status_code=200)
def reset_password(body: PasswordReset):
    """
    使用 token 重置密码。
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        now = datetime.now(tz=timezone.utc).isoformat()

        if get_config().DATABASE_TYPE == "postgresql":
            from psycopg2.extras import DictCursor
            cur_fetch = conn.cursor(cursor_factory=DictCursor)
            cur_fetch.execute("SELECT id, username, password_reset_token_expires FROM users WHERE password_reset_token=%s;", (body.token,))
            row = _wrap_pg_dict(cur_fetch.fetchone())
            cur_fetch.close()
        else:
            cur.execute("SELECT id, username, password_reset_token_expires FROM users WHERE password_reset_token=?;", (body.token,))
            row = cur.fetchone()
            if row:
                row = dict(zip([d[0] for d in cur.description], row))

        if not row:
            cur.close()
            raise HTTPException(status_code=400, detail="无效或过期的重置链接")

        # 检查是否过期
        expires_str = row.get("password_reset_token_expires")
        if expires_str:
            from datetime import datetime as dt
            expires_dt = dt.fromisoformat(expires_str.replace("Z", "+00:00"))
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=timezone.utc)
            if expires_dt < datetime.now(tz=timezone.utc):
                cur.close()
                raise HTTPException(status_code=400, detail="重置链接已过期，请重新申请")

        # 更新密码
        new_hash = _hash_password(body.new_password)
        if get_config().DATABASE_TYPE == "postgresql":
            cur.execute("UPDATE users SET password_hash=%s, password_reset_token=NULL, password_reset_token_expires=NULL, updated_at=%s WHERE id=%s;", (new_hash, datetime.now(tz=timezone.utc), row["id"]))
        else:
            cur.execute("UPDATE users SET password_hash=?, password_reset_token=NULL, password_reset_token_expires=NULL, updated_at=? WHERE id=?;", (new_hash, datetime.now(tz=timezone.utc).isoformat(), row["id"]))
        conn.commit()
        cur.close()

        return {"message": "密码重置成功，请使用新密码登录"}
    finally:
        conn.close()
