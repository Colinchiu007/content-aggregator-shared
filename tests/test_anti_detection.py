"""Tests for RPA anti-detection config."""
import pytest
from content_aggregator_shared.shared.rpa_engine.anti_detection import (
    get_browser_launch_options, human_delay, REAL_USER_AGENTS,
)


class TestGetBrowserLaunchOptions:
    def test_default_options(self):
        opts = get_browser_launch_options()
        assert opts["headless"] is False
        assert opts["channel"] == "chromium"
        assert "args" in opts
        assert isinstance(opts["args"], list)
        assert len(opts["args"]) > 5

    def test_headless_true(self):
        opts = get_browser_launch_options(headless=True)
        assert opts["headless"] is True

    def test_custom_channel(self):
        opts = get_browser_launch_options(channel="chrome")
        assert opts["channel"] == "chrome"

    def test_custom_ua(self):
        opts = get_browser_launch_options(user_agent="Custom-UA/1.0")
        assert opts["user_agent"] == "Custom-UA/1.0"

    def test_default_ua_from_list(self):
        opts = get_browser_launch_options()
        assert opts["user_agent"] in REAL_USER_AGENTS

    def test_extra_args_appended(self):
        opts = get_browser_launch_options(extra_args=["--flag1", "--flag2"])
        assert "--flag1" in opts["args"]
        assert "--flag2" in opts["args"]

    def test_anti_detection_args_present(self):
        opts = get_browser_launch_options()
        args = opts["args"]
        assert "--disable-blink-features=AutomationControlled" in args
        assert "--no-sandbox" in args

    def test_cn_locale(self):
        opts = get_browser_launch_options()
        assert opts["locale"] == "zh-CN"
        assert opts["timezone_id"] == "Asia/Shanghai"

    def test_viewport(self):
        opts = get_browser_launch_options()
        assert opts["viewport"] == {"width": 1920, "height": 1080}

    def test_ignore_default_args(self):
        opts = get_browser_launch_options()
        assert "enable-automation" in opts["ignore_default_args"]


class TestHumanDelay:
    def test_default_range(self):
        delay = human_delay()
        assert 300 <= delay <= 1500

    def test_custom_range(self):
        delay = human_delay(min_ms=1000, max_ms=2000)
        assert 1000 <= delay <= 2000

    def test_same_min_max(self):
        delay = human_delay(min_ms=500, max_ms=500)
        assert delay == 500

    def test_zero_delay(self):
        delay = human_delay(min_ms=0, max_ms=0)
        assert delay == 0

    def test_large_range(self):
        for _ in range(20):
            delay = human_delay(min_ms=100, max_ms=10000)
            assert 100 <= delay <= 10000


class TestRealUserAgents:
    def test_is_list(self):
        assert isinstance(REAL_USER_AGENTS, list)
        assert len(REAL_USER_AGENTS) >= 1

    def test_agents_contain_chrome(self):
        for ua in REAL_USER_AGENTS:
            assert "Chrome" in ua

    def test_agents_contain_valid_platform(self):
        has_windows = any("Windows" in ua for ua in REAL_USER_AGENTS)
        has_mac = any("Macintosh" in ua for ua in REAL_USER_AGENTS)
        assert has_windows or has_mac
