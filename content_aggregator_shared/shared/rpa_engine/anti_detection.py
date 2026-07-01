"""
反检测配置

针对各平台的风控策略，提供浏览器启动参数和操作规范。
"""

from typing import Any

# 真实浏览器 UA 列表（定期更新）
REAL_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def get_browser_launch_options(
    headless: bool = False,
    user_agent: str | None = None,
    channel: str = "chromium",
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    """
    获取浏览器启动参数（反检测配置）

    Args:
        headless: 是否无头模式（RPA 发布必须 False，绕过检测）
        user_agent: 自定义 UA，None 则随机选择
        channel: 浏览器渠道（chromium/chrome/msedge）
        extra_args: 额外启动参数

    Returns:
        Playwright launch_options 字典
    """
    args = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-infobars",
        "--window-size=1920,1080",
        "--disable-extensions",
        "--disable-popup-blocking",
        "--disable-notifications",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-site-isolation-trials",
        "--disable-web-security",  # 注意：仅用于本地 RPA，生产环境慎用
        "--allow-running-insecure-content",
    ]

    if extra_args:
        args.extend(extra_args)

    return {
        "channel": channel,
        "headless": headless,
        "args": args,
        "ignore_default_args": ["enable-automation"],
        "user_agent": user_agent or REAL_USER_AGENTS[0],
        "locale": "zh-CN",
        "timezone_id": "Asia/Shanghai",
        "viewport": {"width": 1920, "height": 1080},
    }


def human_delay(min_ms: int = 300, max_ms: int = 1500) -> int:
    """
    生成模拟人类操作的随机延迟

    Args:
        min_ms: 最小延迟（毫秒）
        max_ms: 最大延迟（毫秒）

    Returns:
        随机延迟值
    """
    import random
    return random.randint(min_ms, max_ms)
