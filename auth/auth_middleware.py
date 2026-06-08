"""
FastAPI 认证中间件 — 依赖注入式鉴权
在路由中使用 Depends(get_current_user) 即可保护接口。
"""

from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from shared.auth.jwt_handler import get_user_from_token

# ---------------------------------------------------------------------------
# 常量 & 工具
# ---------------------------------------------------------------------------
_SAFE_METHODS: List[str] = ["GET", "HEAD", "OPTIONS"]


def _extract_token(request: Request) -> Optional[str]:
    """
    从 Authorization header 中提取 Bearer Token。
    未携带时返回 None（允许可选鉴权场景）。
    """
    auth_header: Optional[str] = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:]


def _raise_401(detail: str = "未登录或 Token 已过期") -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _raise_403(detail: str = "权限不足") -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# 核心依赖：获取当前用户（必须登录）
# ---------------------------------------------------------------------------
async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    FastAPI 依赖：解析 Bearer Token，返回用户信息字典。
    用法：
        @app.get("/api/foo")
        async def foo(user=Depends(get_current_user)):
            ...
    """
    token = _extract_token(request)
    if not token:
        _raise_401("缺少 Authorization Bearer Token")

    user_info = get_user_from_token(token)
    if not user_info:
        _raise_401()

    # 可选：每次请求都查库确认用户仍活跃（性能换安全）
    # 这里不做强制查库，依赖 JWT 有效期 + 用户主动退出/禁用后的 token 过期机制

    return user_info


async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """
    可选鉴权依赖：携带 Token 则解析，未携带则返回 None。
    适用于「登录用户看到更多内容，匿名用户看到公开内容」的场景。
    """
    token = _extract_token(request)
    if not token:
        return None
    return get_user_from_token(token)


# ---------------------------------------------------------------------------
# 配额检查依赖
# ---------------------------------------------------------------------------
async def check_video_quota(request: Request, user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    检查用户视频生成配额（按 subscription_plan 动态判断）。
    使用原子操作避免并发竞态条件。
    返回用户信息字典（同 get_current_user），供端点继续使用。
    用法：
        @router.post("/videos")
        async def create_video(user=Depends(check_video_quota)):
            ...
    """
    from datetime import date

    from shared.auth.config import get_config, get_db_connection

    config = get_config()
    conn = get_db_connection()

    # 使用 SERIALIZABLE 隔离级别防止并发问题
    if config.DATABASE_TYPE == "postgresql":
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)

    cur = conn.cursor()

    try:
        user_id = user["user_id"]

        # 原子操作：重置（如需要）+ 检查配额 + 增加计数，全部在单个 UPDATE 中完成
        if config.DATABASE_TYPE == "postgresql":
            cur.execute("""
                UPDATE user_profiles
                SET videos_used_today = CASE
                    WHEN last_quota_reset IS NULL OR last_quota_reset < CURRENT_DATE
                    THEN 1  -- 跨天了，重置为 1（本次计入）
                    ELSE videos_used_today + 1  -- 同一天，增加计数
                END,
                last_quota_reset = CURRENT_DATE,
                updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                  AND (
                    -- 条件：未超配额（跨天自动重置后肯定未超；同一天时检查）
                    last_quota_reset IS NULL
                    OR last_quota_reset < CURRENT_DATE
                    OR videos_used_today < video_quota
                  )
                RETURNING videos_used_today, video_quota
            """, (user_id,))
        else:
            # SQLite 版本
            cur.execute("""
                UPDATE user_profiles
                SET videos_used_today = CASE
                    WHEN last_quota_reset IS NULL OR last_quota_reset < date('now')
                    THEN 1
                    ELSE videos_used_today + 1
                END,
                last_quota_reset = date('now'),
                updated_at = datetime('now')
                WHERE user_id = ?
                  AND (
                    last_quota_reset IS NULL
                    OR last_quota_reset < date('now')
                    OR videos_used_today < video_quota
                  )
            """, (user_id,))
            conn.commit()

        result = cur.fetchone()

        if not result:
            # UPDATE 未影响任何行 → 配额已用完
            if config.DATABASE_TYPE == "postgresql":
                cur.execute("""
                    SELECT video_quota, videos_used_today
                    FROM user_profiles
                    WHERE user_id = %s
                """, (user_id,))
            else:
                cur.execute("""
                    SELECT video_quota, videos_used_today
                    FROM user_profiles
                    WHERE user_id = ?
                """, (user_id,))
            quota_info = cur.fetchone()
            (quota, used) = quota_info if quota_info else (0, 0)
            if config.DATABASE_TYPE == "postgresql":
                conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"今日视频生成配额已用完（{used}/{quota}）。升级订阅计划以获取更多配额。"
            )

        (used_today, quota) = result
        if config.DATABASE_TYPE == "postgresql":
            conn.commit()

        # 返回更新后的用户信息
        user["quota"] = quota
        user["used_today"] = used_today
        return user

    except HTTPException:
        if config.DATABASE_TYPE == "postgresql":
            conn.rollback()
        raise
    except Exception as e:
        if config.DATABASE_TYPE == "postgresql":
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配额检查失败：{str(e)}"
        )
    finally:
        cur.close()
        conn.close()


# ---------------------------------------------------------------------------
# 角色权限依赖工厂
# ---------------------------------------------------------------------------
def require_role(allowed_roles: List[str]):
    """
    角色鉴权依赖工厂。
    用法：
        @app.get("/api/admin/only")
        async def admin_only(user=Depends(require_role(["admin"])):
            ...
    """
    async def _checker(user: Dict = Depends(get_current_user)) -> Dict:
        if user.get("role") not in allowed_roles:
            _raise_403(f"需要角色 {allowed_roles}，当前角色：{user.get('role')}")
        return user
    return _checker


# 快捷依赖
require_admin = require_role(["admin"])
require_vip = require_role(["admin", "vip"])
require_user = get_current_user  # 任意登录用户均可


# ---------------------------------------------------------------------------
# 中间件方式（可选，用于全局日志/统计，非必须）
# ---------------------------------------------------------------------------
class AuthLoggingMiddleware(BaseHTTPMiddleware):
    """
    全局中间件：记录已登录用户的请求（不阻断请求）。
    如不需要可删除，不影响鉴权功能。
    """

    async def dispatch(self, request: Request, call_next):
        token = _extract_token(request)
        if token:
            user_info = get_user_from_token(token)
            if user_info:
                request.state.user_id = user_info.get("user_id")
                request.state.username = user_info.get("username")
                request.state.role = user_info.get("role")
        response = await call_next(request)
        return response
