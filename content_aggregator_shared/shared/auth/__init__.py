"""
共享认证模块

为 PROJECT-001、002、003 提供统一的认证能力。

使用方式：
    # 在 FastAPI 应用中
    from content_aggregator_shared.shared.auth.auth_middleware import get_current_user

    @app.get("/api/protected")
    async def protected(user=Depends(get_current_user)):
        return {"user": user}

    # 在认证路由中
    from content_aggregator_shared.shared.auth.auth_routes import router as auth_router
    app.include_router(auth_router)
"""

__version__ = "1.0.0"

from content_aggregator_shared.shared.auth.config import AuthConfig, get_config, get_db_connection
from content_aggregator_shared.shared.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_from_token,
)
from content_aggregator_shared.shared.auth.auth_middleware import (
    get_current_user,
    get_current_user_optional,
    require_role,
    require_admin,
    require_vip,
    require_user,
)

__all__ = [
    # 配置
    "AuthConfig",
    "get_config",
    "get_db_connection",
    # JWT
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_user_from_token",
    # 中间件
    "get_current_user",
    "get_current_user_optional",
    "require_role",
    "require_admin",
    "require_vip",
    "require_user",
]
