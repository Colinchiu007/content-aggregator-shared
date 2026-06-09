"""
RPA 发布器基类

提供基于 Playwright 的浏览器自动化发布抽象基类，
子类需实现 login(), check_login(), publish() 方法。

使用 anti_detection.py 的反检测配置进行浏览器初始化。
"""

import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from .anti_detection import get_browser_launch_options, human_delay
from .cookie_manager import CookieManager


class BaseRPAPublisher(ABC):
    """
    RPA 发布器抽象基类

    封装 Playwright 浏览器自动化流程，提供：
    - 浏览器 / 上下文生命周期管理
    - Cookie 持久化钩子（登录态保持）
    - 统一的 login / check_login / publish / close 接口

    Attributes:
        platform: 平台名称（如 "zhihu"、"weibo"），用于 Cookie 存储
        data_dir: 数据目录（Cookie、配置等）
        headless: 是否无头模式（RPA 发布建议 False）
        channel: 浏览器渠道（chromium/chrome/msedge）
        timeout: 页面操作超时（毫秒）
    """

    def __init__(
        self,
        platform: str,
        data_dir: str | Path,
        headless: bool = False,
        channel: str = "chromium",
        timeout: int = 30_000,
    ):
        """
        初始化发布器

        Args:
            platform: 平台名称
            data_dir: 数据目录
            headless: 是否无头模式
            channel: 浏览器渠道
            timeout: 页面操作超时（毫秒）
        """
        self.platform = platform
        self.data_dir = Path(data_dir)
        self.headless = headless
        self.channel = channel
        self.timeout = timeout

        # Cookie 管理器
        self._cookie_manager = CookieManager(data_dir)

        # Playwright 资源
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

        # 确保 Cookie 目录存在
        self._cookie_manager.ensure_dir()

    # ==================== 生命周期 ====================

    def _ensure_browser(self) -> None:
        """确保浏览器实例已启动"""
        if self._browser is not None:
            return

        launch_options = get_browser_launch_options(
            headless=self.headless,
            channel=self.channel,
        )
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(**launch_options)
        logger.info(f"[{self.platform}] 浏览器已启动")

    def _ensure_context(self) -> BrowserContext:
        """确保浏览器上下文已创建（带 Cookie 恢复）"""
        self._ensure_browser()

        if self._context is not None:
            return self._context

        self._context = self._browser.new_context(
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            viewport={"width": 1920, "height": 1080},
            user_agent=self._browser.launch_persistent_context  # generated dynamically
        )
        # 创建新 page（上面 new_context 不自动创建 page）
        if self._page is None:
            self._page = self._context.new_page()
            self._page.set_default_timeout(self.timeout)

        # 恢复已保存的 Cookie
        self._restore_cookies()

        return self._context

    def _ensure_page(self) -> Page:
        """确保 Page 对象就绪"""
        self._ensure_context()
        if self._page is None:
            self._page = self._context.new_page()
            self._page.set_default_timeout(self.timeout)
        return self._page

    # ==================== Cookie 操作 ====================

    def _restore_cookies(self) -> None:
        """从持久化存储恢复 Cookie 到当前浏览器上下文"""
        cookies = self._cookie_manager.load(self.platform)
        if not cookies:
            logger.info(f"[{self.platform}] 无已保存的 Cookie，需要登录")
            return

        if self._context is None:
            return

        self._context.add_cookies(cookies)
        logger.info(f"[{self.platform}] 已恢复 {len(cookies)} 条 Cookie")

    def _save_cookies(self) -> None:
        """将当前浏览器上下文的 Cookie 持久化保存"""
        if self._context is None:
            return

        cookies = self._context.cookies()
        if not cookies:
            logger.warning(f"[{self.platform}] 当前无 Cookie 可保存")
            return

        self._cookie_manager.save(self.platform, cookies)
        logger.info(f"[{self.platform}] 已保存 {len(cookies)} 条 Cookie")

    def _clear_cookies(self) -> None:
        """清除已保存的 Cookie（触发重新登录）"""
        self._cookie_manager.delete(self.platform)
        logger.info(f"[{self.platform}] 已清除 Cookie")

    # ==================== 抽象方法 ====================

    @abstractmethod
    def login(self) -> bool:
        """
        执行平台登录

        Returns:
            True 表示登录成功，False 表示失败
        """
        ...

    @abstractmethod
    def check_login(self) -> bool:
        """
        检查当前登录状态是否有效

        子类应导航到登录态检测页面（如个人中心），
        通过页面元素判断是否仍然在线。

        Returns:
            True 表示登录有效，False 表示已过期
        """
        ...

    @abstractmethod
    def publish(self, article: dict[str, Any]) -> dict[str, Any]:
        """
        发布文章到目标平台

        Args:
            article: 文章数据字典，至少包含：
                - title: 标题
                - content: 正文（HTML 或 Markdown）
                - cover: 封面图 URL（可选）
                - tags: 标签列表（可选）
                - digest: 摘要（可选）

        Returns:
            dict 包含发布结果：
                - success: bool
                - url: 文章链接（可选）
                - article_id: 平台文章 ID（可选）
                - error: 错误信息（可选）
        """
        ...

    # ==================== 统一入口 ====================

    def authorize(self) -> bool:
        """
        统一认证入口

        1. 先检查已保存的 Cookie 是否有效
        2. 无效则执行完整登录流程
        3. 登录成功后保存 Cookie

        Returns:
            True 表示认证成功，False 表示失败
        """
        self._ensure_page()

        # 尝试用已有 Cookie 恢复登录态
        if self._cookie_manager.exists(self.platform):
            logger.info(f"[{self.platform}] 检测到已保存的 Cookie，检查登录态...")
            if self.check_login():
                logger.info(f"[{self.platform}] Cookie 有效，无需重新登录")
                return True
            else:
                logger.info(f"[{self.platform}] Cookie 已过期，需要重新登录")
                self._clear_cookies()
        else:
            logger.info(f"[{self.platform}] 未检测到 Cookie，需要登录")

        # 执行完整登录
        success = self.login()
        if success:
            self._save_cookies()
            logger.info(f"[{self.platform}] 登录成功，Cookie 已保存")
        else:
            logger.error(f"[{self.platform}] 登录失败")
        return success

    def publish_with_auth(self, article: dict[str, Any]) -> dict[str, Any]:
        """
        带自动认证的发布入口

        1. 自动检查 / 执行登录
        2. 发布文章
        3. 更新 Cookie

        Args:
            article: 文章数据字典

        Returns:
            发布结果字典
        """
        # 确保已认证
        if not self.authorize():
            return {
                "success": False,
                "error": f"[{self.platform}] 认证失败，无法发布",
            }

        # 模拟人类操作延迟
        time.sleep(human_delay() / 1000.0)

        # 发布
        result = self.publish(article)

        # 发布完成后保存最新 Cookie
        if result.get("success"):
            self._save_cookies()

        return result

    # ==================== 清理 ====================

    def close(self) -> None:
        """
        释放浏览器资源

        在发布流程结束后调用，确保：
        1. 保存最新 Cookie
        2. 关闭浏览器上下文
        3. 关闭浏览器实例
        4. 停止 Playwright 引擎
        """
        try:
            # 保存最新 Cookie
            if self._context and self._cookie_manager.exists(self.platform):
                self._save_cookies()

            # 关闭 page
            if self._page:
                try:
                    self._page.close()
                except Exception:
                    pass
                self._page = None

            # 关闭上下文
            if self._context:
                try:
                    self._context.close()
                except Exception:
                    pass
                self._context = None

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

            logger.info(f"[{self.platform}] 浏览器资源已释放")

        except Exception as e:
            logger.error(f"[{self.platform}] 关闭浏览器时出错: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出时自动清理"""
        self.close()
        return False