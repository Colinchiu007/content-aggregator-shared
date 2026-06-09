"""验证 rpa_engine 三个新文件的基本功能"""
import os
import sys
import tempfile

# 一次性导入所有需要测试的类
from rpa_engine import BaseRPAPublisher, BrowserPool, CookieManager, get_browser_launch_options


def test_imports():
    print("  ✓ BaseRPAPublisher 导入成功")
    print("  ✓ BrowserPool 导入成功")
    print("  ✓ CookieManager 导入成功")
    print("  ✓ get_browser_launch_options 导入成功")


def test_cookie_manager():
    tmpdir = tempfile.mkdtemp()
    cm = CookieManager(tmpdir, master_password="test-key-123")
    print("  ✓ CookieManager 初始化成功")

    # save
    test_cookies = [{"name": "session", "value": "abc123", "domain": ".example.com"}]
    cm.save("test_platform", test_cookies)
    print("  ✓ Cookie 保存成功")

    # exists
    assert cm.exists("test_platform")
    print("  ✓ Cookie 文件存在检测通过")

    # load
    loaded = cm.load("test_platform")
    assert len(loaded) == 1
    assert loaded[0]["name"] == "session"
    assert loaded[0]["value"] == "abc123"
    print("  ✓ Cookie 加载+解密验证通过")

    # list_platforms
    platforms = cm.list_platforms()
    assert "test_platform" in platforms
    print(f"  ✓ 平台列表包含 test_platform: {platforms}")

    # delete
    assert cm.delete("test_platform")
    assert not cm.exists("test_platform")
    print("  ✓ Cookie 删除成功")


def test_browser_pool():
    tmpdir = tempfile.mkdtemp()
    bp1 = BrowserPool(data_dir=tmpdir)
    bp2 = BrowserPool(data_dir="/some/other/path")
    assert bp1 is bp2
    print("  ✓ BrowserPool 是单例 (id一致)")
    assert bp1.active_count == 0
    assert not bp1.is_running
    print("  ✓ 初始状态正确 (active_count=0, is_running=False)")
    assert bp1.list_active_accounts() == []
    print("  ✓ 活跃账号列表为空")


def test_base_publisher():
    assert BaseRPAPublisher.__abstractmethods__ == frozenset({"login", "check_login", "publish"})
    print("  ✓ 基类抽象方法正确: login, check_login, publish")
    assert "close" not in BaseRPAPublisher.__abstractmethods__
    print("  ✓ close() 有默认实现（非抽象）")
    assert hasattr(BaseRPAPublisher, "authorize")
    assert hasattr(BaseRPAPublisher, "publish_with_auth")
    print("  ✓ authorize() 和 publish_with_auth() 统一入口已定义")

    # 子类继承验证
    class MockPublisher(BaseRPAPublisher):
        def login(self): return True
        def check_login(self): return True
        def publish(self, article): return {"success": True, "url": "https://example.com"}

    tmpdir = tempfile.mkdtemp()
    pub = MockPublisher(platform="mock", data_dir=tmpdir)
    assert isinstance(pub, BaseRPAPublisher)
    assert isinstance(pub, BaseRPAPublisher)
    print("  ✓ 子类继承正确")

    # 验证 context manager
    with MockPublisher(platform="mock2", data_dir=tmpdir) as p:
        assert p.platform == "mock2"
    print("  ✓ 上下文管理器支持正确")


if __name__ == "__main__":
    print("=" * 50)
    print("rpa_engine 模块验证测试")
    print("=" * 50)
    print()

    print("=== 测试 1: 模块导入 ===")
    test_imports()
    print()

    print("=== 测试 2: CookieManager (加密存储) ===")
    test_cookie_manager()
    print()

    print("=== 测试 3: BrowserPool (单例) ===")
    test_browser_pool()
    print()

    print("=== 测试 4: BaseRPAPublisher (抽象基类) ===")
    test_base_publisher()
    print()

    print("=" * 50)
    print("全部测试通过 ✓")
    print("=" * 50)
