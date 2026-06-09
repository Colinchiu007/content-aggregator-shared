"""
浏览器实例池（单例）

管理多个 Playwright 浏览器上下文实例，
按 account_id 分配和回收，支持统一清理。

避免每个发布任务都从头启动浏览器，
减少资源开销和登录次数。
"""

import threading
from pathlib import Path
from typing import Any

from loguru import logger
from playwright.sync_api import Browser, BrowserContext, sync_playwright

from .anti_detection import get_browser_launch_options


class BrowserPool:
    """
    浏览器实例池（单例）

    功能：
    - acquire(account_id) → 获取或创建浏览器上下文
    - release(account_id) → 释放指定账号的上下文
    - close_all() → 关闭所有资源

    线程安全（使用可重入锁）。
    """

    _instance: "BrowserPool | None" = None
    _lock = threading.RLock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "BrowserPool":
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        data_dir: str | Path | None = None,
        headless: bool = False,
        channel: str = "chromium",
        timeout: int = 30_000,
    ):
        """
        初始化浏览器池

        Args:
            data_dir: 数据目录（用于 Cookie 持久化，可选）
            headless: 是否无头模式
            channel: 浏览器渠道
            timeout: 页面操作超时（毫秒）
        """
        with self._lock:
            if self._initialized:
                return

            self.data_dir = Path(data_dir) if data_dir else Path.cwd() / ".rpa_data"
            self.headless = headless
            self.channel = channel
            self.timeout = timeout

            # Playwright 引擎实例（共用）
            self._playwright = None
            self._browser: Browser | None = None

            # 账号上下文映射：{account_id: BrowserContext}
            self._contexts: dict[str, BrowserContext] = {}

            # 账号页面映射：{account_id: Page}
            self._pages: dict[str, Any] = {}

            # 已关闭标记
            self._closed = False

            self._initialized = True
            logger.info("BrowserPool 已初始化")

    # ==================== 资源管理 ====================

    def _ensure_playwright(self) -> Browser:
        """确保 Playwright 和浏览器实例已启动"""
        if self._browser is not None:
            return self._browser

        launch_options = get_browser_launch_options(
            headless=self.headless,
            channel=self.channel,
        )
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(**launch_options)
        logger.info("BrowserPool: 浏览器已启动")
        return self._browser

    def acquire(self, account_id: str) -> BrowserContext:
        """
        获取指定账号的浏览器上下文

        如果该账号已有上下文，直接返回已有的。
        否则创建一个新的上下文（共享同一个浏览器实例）。

        Args:
            account_id: 账号唯一标识

        Returns:
            BrowserContext 实例

        Raises:
            RuntimeError: 如果池已关闭
        """
        if self._closed:
            raise RuntimeError("BrowserPool 已关闭，无法获取新上下文")

        with self._lock:
            # 如果已有上下文，直接返回
            if account_id in self._contexts:
                logger.debug(f"BrowserPool: 复用账号 {account_id} 的上下文")
                context = self._contexts[account_id]
                # 确保浏览器进程未崩溃
                try:
                    context.pages  # 轻量探活
                    return context
                except Exception:
                    logger.warning(f"BrowserPool: 账号 {account_id} 的上下文已失效，重新创建")
                    del self._contexts[account_id]
                    if account_id in self._pages:
                        del self._pages[account_id]

            # 启动浏览器（共享实例）
            browser = self._ensure_playwright()

            # 创建新的独立上下文（隔离 Cookie/存储）
            context = browser.new_context(
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
            )

            # 创建默认 page
            page = context.new_page()
            page.set_default_timeout(self.timeout)

            self._contexts[account_id] = context
            self._pages[account_id] = page

            logger.info(f"BrowserPool: 为账号 {account_id} 创建新上下文")
            return context

    def get_page(self, account_id: str) -> Any:
        """
        获取指定账号的 Page 对象

        Args:
            account_id: 账号唯一标识

        Returns:
            Page 对象
        """
        self.acquire(account_id)  # 确保上下文存在
        return self._pages.get(account_id)

    def release(self, account_id: str) -> None:
        """
        释放指定账号的浏览器上下文

        关闭上下文并清理页面对象。

        Args:
            account_id: 账号唯一标识
        """
        with self._lock:
            # 关闭 page
            if account_id in self._pages:
                try:
                    self._pages[account_id].close()
                except Exception:
                    pass
                del self._pages[account_id]

            # 关闭上下文
            if account_id in self._contexts:
                try:
                    self._contexts[account_id].close()
                except Exception:
                    pass
                del self._contexts[account_id]
                logger.info(f"BrowserPool: 已释放账号 {account_id} 的上下文")

    def close_all(self) -> None:
        """
        关闭所有浏览器资源

        1. 关闭所有账号的上下文
        2. 关闭浏览器实例
        3. 停止 Playwright 引擎
        """
        with self._lock:
            if self._closed:
                return
            self._closed = True

            # 关闭所有页面和上下文
            for account_id in list(self._pages.keys()):
                try:
                    self._pages[account_id].close()
                except Exception:
                    pass
            self._pages.clear()

            for account_id in list(self._contexts.keys()):
                try:
                    self._contexts[account_id].close()
                except Exception:
                    pass
            self._contexts.clear()

            # 关闭浏览器
            if self._browser:
                try:
                    self._browser.close()
                except Exception:
                    pass
                self._browser = None

            # 停止 Playwright
            if self._playwright:
                try:
                    self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None

            logger.info("BrowserPool: 所有资源已释放")

    # ==================== 查询状态 ====================

    @property
    def active_count(self) -> int:
        """当前活跃的上下文数量"""
        return len(self._contexts)

    @property
    def is_running(self) -> bool:
        """浏览器池是否正在运行"""
        return not self._closed and self._browser is not None

    def list_active_accounts(self) -> list[str]:
        """获取所有活跃的账号 ID 列表"""
        return list(self._contexts.keys())

    # ==================== 清理钩子 ====================

    def __del__(self):
        """析构时自动关闭"""
        try:
            self.close_all()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()
        return False