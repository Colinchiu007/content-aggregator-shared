"""
代理模块 — 从 MediaCrawler proxy 适配

提供：
- ProxyRefreshMixin: 混入类，给 API Client 自动代理轮换能力
- ProxyIpPool: 代理 IP 池（带过期管理、多提供商、有效性验证）
- create_ip_pool(): 工厂函数
- IpInfoModel: 代理 IP 数据模型

使用:
    class MyClient(ProxyRefreshMixin):
        async def fetch(self):
            await self._refresh_proxy_if_expired()
            # 用 self.proxy 发起请求
"""

from .ip_pool import (
    IpInfoModel,
    BaseProxyProvider,
    KuaiDaiLiProvider,
    StaticProxyProvider,
    ProxyIpPool,
    create_ip_pool,
    IP_PROVIDER_MAP,
)

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ProxyRefreshMixin:
    """
    代理自动刷新混入类

    用法:
        class MyApiClient(ProxyRefreshMixin):
            async def request(self, ...):
                await self._refresh_proxy_if_expired()
                # 用 self.proxy 配置 httpx client
                ...

    从 MediaCrawler proxy/proxy_mixin.py 适配：
    - _refresh_proxy_if_expired() 保留原始方法名
    - init_proxy_pool() 保留原始方法名
    - 支持异步上下文
    移除：proxychains 模式（不适合本架构）、socks5 支持（可扩展）
    """

    def __init__(self):
        self.proxy_ip_pool: Optional[ProxyIpPool] = None
        self.proxy: Optional[str] = None

    def init_proxy_pool(self, proxy_ip_pool: ProxyIpPool) -> None:
        """初始化代理池（与 MediaCrawler 同名方法一致）"""
        self.proxy_ip_pool = proxy_ip_pool
        logger.info(f"[ProxyRefreshMixin] 代理池已初始化（池大小: {proxy_ip_pool.pool_size}）")

    async def _refresh_proxy_if_expired(self) -> None:
        """检查当前代理是否过期，过期则自动刷新"""
        if self.proxy_ip_pool is None:
            return

        if self.proxy_ip_pool.is_current_proxy_expired():
            logger.info("[ProxyRefreshMixin] 当前代理已过期，刷新...")
            ip_info = await self.proxy_ip_pool.get_or_refresh_proxy()
            self.proxy = ip_info.url
            logger.info(f"[ProxyRefreshMixin] 代理已切换至 {ip_info.ip}:{ip_info.port}")

    async def force_refresh_proxy(self) -> None:
        """强制刷新代理（外部调用，如遇到 403/429 时）"""
        if self.proxy_ip_pool is None:
            logger.warning("[ProxyRefreshMixin] 代理池未初始化，无法刷新")
            return

        logger.info("[ProxyRefreshMixin] 强制刷新代理...")
        ip_info = await self.proxy_ip_pool.get_proxy()
        if ip_info:
            self.proxy = ip_info.url
            logger.info(f"[ProxyRefreshMixin] 代理已切换至 {ip_info.ip}:{ip_info.port}")
        else:
            logger.warning("[ProxyRefreshMixin] 代理池为空，无法获取新代理")


__all__ = [
    # 数据模型
    "IpInfoModel",

    # 代理提供者
    "BaseProxyProvider",
    "KuaiDaiLiProvider",
    "StaticProxyProvider",

    # IP 池
    "ProxyIpPool",
    "create_ip_pool",
    "IP_PROVIDER_MAP",

    # 混入类
    "ProxyRefreshMixin",
]
