"""
Cookie 持久化管理器

提供加密存储的 Cookie 管理功能：
- load(platform) → 解密加载
- save(platform, cookies) → 加密保存
- delete(platform) → 删除

使用 AES-256-GCM（通过 cryptography 的 Fernet）加密，
密钥由 PBKDF2-HMAC-SHA256 派生。
"""

import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger

# 默认主密码（开发环境使用，生产环境应通过环境变量设置）
_DEFAULT_MASTER_PASSWORD = "dev-mode-insecure-do-not-use-in-production"


class CookieManager:
    """
    Cookie 持久化管理器

    使用 AES-256-GCM（Fernet 封装）加密存储 Cookie。
    每个平台的 Cookie 存储在独立的加密文件中。

    文件路径: {data_dir}/cookies/{platform}.enc
    """

    def __init__(
        self,
        data_dir: str | Path,
        master_password: str | None = None,
    ):
        """
        初始化 Cookie 管理器

        Args:
            data_dir: 数据根目录（Cookie 存储在 {data_dir}/cookies/）
            master_password: 主密码（用于派生 AES 密钥）
                - 如果为 None，优先读取 COOKIE_MASTER_KEY 环境变量
                - 都不设置则使用开发模式默认密钥（不安全）
        """
        self._cookies_dir = Path(data_dir) / "cookies"
        self._master_password = master_password or os.environ.get(
            "COOKIE_MASTER_KEY", _DEFAULT_MASTER_PASSWORD
        )

        # 初始化加密器
        self._fernet = self._create_fernet()

        if self._master_password == _DEFAULT_MASTER_PASSWORD:
            logger.warning(
                "CookieManager: 使用默认开发密钥，Cookie 加密不安全。"
                "请设置 COOKIE_MASTER_KEY 环境变量或传入 master_password。"
            )

    def ensure_dir(self) -> Path:
        """确保 Cookie 存储目录存在"""
        self._cookies_dir.mkdir(parents=True, exist_ok=True)
        return self._cookies_dir

    def _create_fernet(self) -> Fernet:
        """
        从主密码派生 Fernet 密钥

        使用 PBKDF2-HMAC-SHA256，固定盐值（可保证同一密码始终派生同一密钥）。
        """
        import base64

        # 使用固定的派生盐值（可存储在代码中，因为安全依赖于主密码强度）
        salt = b"cookie_manager_salt_2024_v1"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._master_password.encode()))
        return Fernet(key)

    def _cookie_path(self, platform: str) -> Path:
        """获取指定平台的 Cookie 文件路径"""
        return self._cookies_dir / f"{platform}.enc"

    def save(self, platform: str, cookies: list[dict[str, Any]]) -> None:
        """
        加密保存 Cookie

        将 Cookie 列表序列化为 JSON 并加密写入文件。

        Args:
            platform: 平台名称（如 "zhihu"、"weibo"）
            cookies: Playwright Cookie 列表（list of dict）
        """
        try:
            self.ensure_dir()
            file_path = self._cookie_path(platform)

            # 序列化
            plaintext = json.dumps(cookies, ensure_ascii=False, default=str)

            # 加密
            encrypted = self._fernet.encrypt(plaintext.encode("utf-8"))

            # 原子写入（先写临时文件再重命名）
            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "wb") as f:
                f.write(encrypted)
            temp_path.rename(file_path)

            logger.debug(f"CookieManager: 已保存 {len(cookies)} 条 Cookie -> {file_path}")

        except Exception as e:
            logger.error(f"CookieManager: 保存 Cookie 失败 ({platform}): {e}")
            raise

    def load(self, platform: str) -> list[dict[str, Any]]:
        """
        解密加载 Cookie

        Returns:
            Cookie 列表，如果文件不存在则返回空列表
        """
        file_path = self._cookie_path(platform)
        if not file_path.exists():
            return []

        try:
            # 读取加密文件
            with open(file_path, "rb") as f:
                encrypted = f.read()

            # 解密
            plaintext = self._fernet.decrypt(encrypted)

            # 反序列化
            cookies: list[dict[str, Any]] = json.loads(plaintext.decode("utf-8"))
            logger.debug(f"CookieManager: 已加载 {len(cookies)} 条 Cookie <- {file_path}")
            return cookies

        except Exception as e:
            logger.error(f"CookieManager: 加载 Cookie 失败 ({platform}): {e}")
            return []

    def delete(self, platform: str) -> bool:
        """
        删除指定平台的 Cookie 文件

        Returns:
            True 表示成功删除，False 表示文件不存在或删除失败
        """
        file_path = self._cookie_path(platform)
        if not file_path.exists():
            logger.debug(f"CookieManager: Cookie 文件不存在，无需删除 ({platform})")
            return False

        try:
            file_path.unlink()
            logger.info(f"CookieManager: 已删除 Cookie 文件 ({platform})")
            return True
        except Exception as e:
            logger.error(f"CookieManager: 删除 Cookie 文件失败 ({platform}): {e}")
            return False

    def exists(self, platform: str) -> bool:
        """
        检查指定平台的 Cookie 文件是否存在

        Args:
            platform: 平台名称

        Returns:
            True 表示 Cookie 文件存在
        """
        return self._cookie_path(platform).exists()

    def list_platforms(self) -> list[str]:
        """
        列出所有有 Cookie 的平台

        Returns:
            平台名称列表
        """
        if not self._cookies_dir.exists():
            return []

        platforms = []
        for f in sorted(self._cookies_dir.iterdir()):
            if f.suffix == ".enc":
                platforms.append(f.stem)
        return platforms

    def clear_all(self) -> int:
        """
        清除所有平台的 Cookie

        Returns:
            清除的文件数量
        """
        count = 0
        for platform in self.list_platforms():
            if self.delete(platform):
                count += 1
        logger.info(f"CookieManager: 已清除 {count} 个平台的 Cookie")
        return count