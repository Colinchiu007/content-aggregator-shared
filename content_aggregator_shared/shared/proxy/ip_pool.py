"""
代理 IP 池 — 从 MediaCrawler proxy_ip_pool.py 适配

提供多提供商代理获取、有效性验证、过期轮换、tenacity 重试。

使用:
    pool = await create_ip_pool("kuaidaili", pool_count=10)
    proxy = await pool.get_proxy()
    # 用 proxy.ip / proxy.port 配置 httpx client
    if pool.is_current_proxy_expired():
        new_proxy = await pool.get_or_refresh_proxy()
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# ── 数据模型 ─────────────────────────────────────────


@dataclass
class IpInfoModel:
    """代理 IP 信息"""
    ip: str
    port: int
    user: str = ""
    password: str = ""
    provider: str = "unknown"
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def url(self) -> str:
        """HTTP 代理 URL"""
        if self.user and self.password:
            return f"http://{self.user}:{self.password}@{self.ip}:{self.port}"
        return f"http://{self.ip}:{self.port}"

    @property
    def is_expired(self) -> bool:
        """是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at

    def is_valid(self, test_url: str = "https://httpbin.org/ip", timeout: int = 10) -> bool:
        """验证代理是否可用"""
        try:
            resp = httpx.get(test_url, proxies=self.url, timeout=timeout)
            return resp.status_code == 200
        except Exception:
            return False

    async def async_is_valid(self, test_url: str = "https://httpbin.org/ip",
                             timeout: int = 10) -> bool:
        """异步验证代理是否可用"""
        try:
            async with httpx.AsyncClient(proxies=self.url, timeout=timeout) as client:
                resp = await client.get(test_url)
                return resp.status_code == 200
        except Exception:
            return False


# ── 代理提供者 ──────────────────────────────────────


class BaseProxyProvider:
    """代理提供者基类"""

    def __init__(self, name: str):
        self.name = name

    async def fetch(self, count: int = 5) -> list[IpInfoModel]:
        """获取一批代理 IP"""
        raise NotImplementedError


class KuaiDaiLiProvider(BaseProxyProvider):
    """快代理"""

    def __init__(self, api_url: str = "", api_key: str = ""):
        super().__init__("kuaidaili")
        self.api_url = api_url
        self.api_key = api_key

    async def fetch(self, count: int = 5) -> list[IpInfoModel]:
        if not self.api_url:
            logger.warning("[Proxy] 快代理 API URL 未配置，返回空池")
            return []
        url = f"{self.api_url}?count={count}&type=json&key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                data = resp.json()
            if data.get("code") != 0:
                return []
            proxies = []
            for item in data.get("data", []):
                proxies.append(IpInfoModel(
                    ip=item["ip"],
                    port=int(item["port"]),
                    provider=self.name,
                    expires_at=datetime.now() + timedelta(minutes=3),
                ))
            return proxies
        except Exception as e:
            logger.warning(f"[Proxy] 快代理获取失败: {e}")
            return []


class StaticProxyProvider(BaseProxyProvider):
    """静态代理（固定地址）"""

    def __init__(self, static_url: str = ""):
        super().__init__("static")
        self.static_url = static_url

    async def fetch(self, count: int = 5) -> list[IpInfoModel]:
        if not self.static_url:
            return []
        # 格式: http://user:pass@ip:port 或 http://ip:port
        url = self.static_url.replace("http://", "").replace("https://", "")
        user = password = ""
        if "@" in url:
            creds, addr = url.split("@", 1)
            if ":" in creds:
                user, password = creds.split(":", 1)
            ip, port = addr.rsplit(":", 1)
        else:
            ip, port = url.rsplit(":", 1)
        return [IpInfoModel(
            ip=ip,
            port=int(port),
            user=user,
            password=password,
            provider=self.name,
            expires_at=datetime.now() + timedelta(hours=1),
        )]


IP_PROVIDER_MAP: dict[str, Callable[..., BaseProxyProvider]] = {
    "kuaidaili": lambda **kw: KuaiDaiLiProvider(**kw),
    "static": lambda **kw: StaticProxyProvider(**kw),
}

# ── 代理 IP 池 ──────────────────────────────────────


class ProxyIpPool:
    """代理 IP 池 — 带有效期管理和自动轮换"""

    def __init__(self, provider: BaseProxyProvider, pool_count: int = 10,
                 enable_validate: bool = True, expiry_seconds: int = 180):
        self.provider = provider
        self.pool_count = pool_count
        self.enable_validate = enable_validate
        self.expiry_seconds = expiry_seconds
        self._pool: list[IpInfoModel] = []
        self._current: Optional[IpInfoModel] = None
        self._last_refresh: Optional[datetime] = None

    def load_proxies(self, proxies: list[IpInfoModel]) -> None:
        """加载一批代理到池中"""
        self._pool.extend(proxies)
        logger.info(f"[ProxyIpPool] 池加载 {len(proxies)} 个代理 (总量: {len(self._pool)})")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.HTTPError, ConnectionError)),
    )
    async def get_proxy(self) -> Optional[IpInfoModel]:
        """从池中获取一个代理（随机选择 + 验证）"""
        if not self._pool:
            logger.info("[ProxyIpPool] 池为空，尝试从 Provider 获取")
            proxies = await self.provider.fetch(self.pool_count)
            if proxies:
                self.load_proxies(proxies)
            else:
                return None

        # 随机选择
        random.shuffle(self._pool)
        proxy = self._pool.pop(0)

        # 验证
        if self.enable_validate:
            valid = await proxy.async_is_valid()
            if not valid:
                logger.warning(f"[ProxyIpPool] 代理 {proxy.ip}:{proxy.port} 无效，跳过")
                return await self.get_proxy()  # 递归重试

        self._current = proxy
        self._last_refresh = datetime.now()
        return proxy

    def is_current_proxy_expired(self) -> bool:
        """当前代理是否过期"""
        if self._current is None:
            return True
        if self._current.expires_at is None:
            return False
        return datetime.now() >= self._current.expires_at

    async def get_or_refresh_proxy(self) -> IpInfoModel:
        """获取当前代理，过期则刷新"""
        if self.is_current_proxy_expired():
            proxy = await self.get_proxy()
            if proxy is None:
                raise RuntimeError("代理池为空，无法获取新代理")
            return proxy
        assert self._current is not None
        return self._current

    @property
    def pool_size(self) -> int:
        return len(self._pool)

    def clear(self) -> None:
        self._pool.clear()
        self._current = None
        self._last_refresh = None


async def create_ip_pool(
    provider_name: str = "static",
    pool_count: int = 10,
    enable_validate_ip: bool = True,
    **provider_kwargs,
) -> ProxyIpPool:
    """
    工厂函数 — 创建代理 IP 池

    Args:
        provider_name: 提供者名称 (kuaidaili / static)
        pool_count: 池大小
        enable_validate_ip: 是否验证代理有效性
        **provider_kwargs: 传递给提供者的参数

    Returns:
        ProxyIpPool 实例
    """
    provider_cls = IP_PROVIDER_MAP.get(provider_name)
    if not provider_cls:
        supported = ", ".join(IP_PROVIDER_MAP)
        raise ValueError(f"不支持的代理提供者: {provider_name!r}。支持: {supported}")

    provider = provider_cls(**provider_kwargs)
    pool = ProxyIpPool(
        provider=provider,
        pool_count=pool_count,
        enable_validate=enable_validate_ip,
    )
    return pool
