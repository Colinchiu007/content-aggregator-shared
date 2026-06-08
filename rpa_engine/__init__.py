"""
RPA 引擎模块

提供浏览器自动化发布的基础设施：
- BaseRPAPublisher: RPA 发布器基类
- BrowserPool: 浏览器实例池管理
- CookieManager: Cookie/登录态持久化
- AntiDetection: 反检测配置
"""

from .base import BaseRPAPublisher
from .browser_pool import BrowserPool
from .cookie_manager import CookieManager
from .anti_detection import get_browser_launch_options

__all__ = [
    "BaseRPAPublisher",
    "BrowserPool",
    "CookieManager",
    "get_browser_launch_options",
]
