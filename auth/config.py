"""
认证模块配置管理

支持多数据库类型（PostgreSQL / SQLite），各项目通过环境变量或配置文件覆盖。
"""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class AuthConfig:
    """认证模块配置"""

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # 数据库类型：postgresql | sqlite
    DATABASE_TYPE: str = "postgresql"

    # PostgreSQL 连接
    DATABASE_URL: str = ""

    # SQLite 路径
    SQLITE_PATH: str = "./data/user.db"

    # 密码哈希
    PASSWORD_HASH_SCHEME: str = "pbkdf2_sha256"


def _load_config_from_env() -> AuthConfig:
    """从环境变量加载配置"""
    return AuthConfig(
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production"),
        JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256"),
        ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7)),
        REFRESH_TOKEN_EXPIRE_DAYS=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30)),
        DATABASE_TYPE=os.getenv("DATABASE_TYPE", "postgresql"),
        DATABASE_URL=os.getenv("DATABASE_URL", ""),
        SQLITE_PATH=os.getenv("SQLITE_PATH", "./data/user.db"),
    )


def _load_config_from_yaml(yaml_path: str) -> AuthConfig | None:
    """从 YAML 配置文件加载（可选）"""
    try:
        import yaml
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        auth = data.get("auth", {})
        if not auth:
            return None
        return AuthConfig(
            JWT_SECRET_KEY=auth.get("jwt_secret", "dev-secret-change-in-production"),
            JWT_ALGORITHM=auth.get("jwt_algorithm", "HS256"),
            ACCESS_TOKEN_EXPIRE_MINUTES=int(auth.get("access_token_expire_minutes", 60 * 24 * 7)),
            REFRESH_TOKEN_EXPIRE_DAYS=int(auth.get("refresh_token_expire_days", 30)),
            DATABASE_TYPE=auth.get("database_type", "postgresql"),
            DATABASE_URL=auth.get("database_url", ""),
            SQLITE_PATH=auth.get("sqlite_path", "./data/user.db"),
        )
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_config() -> AuthConfig:
    """
    获取认证配置（优先环境变量，其次 YAML 文件，最后默认值）

    调用顺序：
    1. 环境变量（最高优先级）
    2. 项目 config.yaml 中的 auth 配置
    3. 默认值
    """
    # 1. 尝试从环境变量加载
    env_config = _load_config_from_env()
    if env_config.JWT_SECRET_KEY != "dev-secret-change-in-production":
        return env_config

    # 2. 尝试从 YAML 加载（各项目的 config.yaml）
    # 查找项目根目录的 config.yaml
    project_dirs = [
        os.path.join(os.path.dirname(__file__), "..", "..", "content-aggregator"),
        os.path.join(os.path.dirname(__file__), "..", "..", "projects", "PROJECT-002-mpt-saas", "MoneyPrinterTurbo"),
        os.path.join(os.path.dirname(__file__), "..", "..", "projects", "PROJECT-003-multi-publish"),
    ]

    for project_dir in project_dirs:
        yaml_path = os.path.join(project_dir, "config", "config.yaml")
        if os.path.exists(yaml_path):
            yaml_config = _load_config_from_yaml(yaml_path)
            if yaml_config:
                return yaml_config

    # 3. 返回环境变量配置（使用默认值）
    return env_config


def get_db_connection():
    """
    根据配置返回数据库连接

    支持：
    - PostgreSQL: 返回 psycopg2 连接
    - SQLite: 返回 sqlite3 连接
    """
    config = get_config()

    if config.DATABASE_TYPE == "sqlite":
        import sqlite3
        os.makedirs(os.path.dirname(config.SQLITE_PATH) or ".", exist_ok=True)
        conn = sqlite3.connect(config.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    # PostgreSQL
    import psycopg2
    return psycopg2.connect(config.DATABASE_URL)


def get_pwd_context():
    """获取密码哈希上下文"""
    from passlib.context import CryptContext
    return CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
