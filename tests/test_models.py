"""Tests for content-aggregator-shared data models."""
import pytest
from datetime import datetime, timedelta
from content_aggregator_shared.shared.wechat_mp.models import (
    PlatformType, TaskStatus, PublishResult, PublishTask, PlatformAccount,
)


class TestPlatformType:
    def test_enum_values(self):
        assert PlatformType.WECHAT_MP.value == "wechat_mp"
        assert PlatformType.ZHIHU.value == "zhihu"
        assert PlatformType.WEIBO.value == "weibo"
        assert PlatformType.DOUYIN.value == "douyin"

    def test_enum_members(self):
        assert len(PlatformType) == 4


class TestTaskStatus:
    def test_enum_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"

    def test_finished_enums_have_correct_values(self):
        """TaskStatus is a pure Enum — is_finished() lives on PublishTask."""
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestPublishResult:
    def test_success_result(self):
        r = PublishResult(success=True, platform="wechat_mp", article_id="123", url="https://mp.weixin.qq.com/123")
        assert r.success is True
        assert r.platform == "wechat_mp"
        assert r.article_id == "123"
        assert r.url == "https://mp.weixin.qq.com/123"
        assert r.error is None
        assert r.duration == 0.0

    def test_failure_result(self):
        r = PublishResult(success=False, platform="wechat_mp", error="token expired")
        assert r.success is False
        assert r.error == "token expired"
        assert r.article_id is None
        assert r.url is None

    def test_with_duration(self):
        r = PublishResult(success=True, platform="wechat_mp", duration=3.5)
        assert r.duration == 3.5


class TestPublishTask:
    def test_default_values(self):
        task = PublishTask(id="1", title="Test", content="Hello", platforms=[PlatformType.WECHAT_MP])
        assert task.status == TaskStatus.PENDING
        assert task.results == {}
        assert task.retry_count == 0
        assert task.max_retries == 3
        assert task.metadata == {}
        assert task.scheduled_at is None

    def test_is_finished_pending(self):
        task = PublishTask(id="1", title="T", content="C", platforms=[PlatformType.WECHAT_MP])
        assert not task.is_finished()

    def test_is_finished_success(self):
        task = PublishTask(id="1", title="T", content="C", platforms=[PlatformType.WECHAT_MP],
                           status=TaskStatus.SUCCESS)
        assert task.is_finished()

    def test_is_finished_failed(self):
        task = PublishTask(id="1", title="T", content="C", platforms=[PlatformType.WECHAT_MP],
                           status=TaskStatus.FAILED)
        assert task.is_finished()

    def test_to_dict(self):
        task = PublishTask(
            id="task-1",
            title="文章标题",
            content="内容",
            platforms=[PlatformType.WECHAT_MP, PlatformType.ZHIHU],
            status=TaskStatus.RUNNING,
            results={
                PlatformType.WECHAT_MP: PublishResult(
                    success=True, platform="wechat_mp", url="https://mp.weixin.qq.com/1"
                ),
            },
            retry_count=1,
        )
        d = task.to_dict()
        assert d["id"] == "task-1"
        assert d["title"] == "文章标题"
        assert d["status"] == "running"
        assert "wechat_mp" in d["results"]
        assert d["results"]["wechat_mp"]["success"] is True
        assert d["results"]["wechat_mp"]["url"] == "https://mp.weixin.qq.com/1"
        assert d["retry_count"] == 1
        assert "created_at" in d

    def test_to_dict_empty_results(self):
        task = PublishTask(id="1", title="T", content="C", platforms=[PlatformType.WECHAT_MP])
        d = task.to_dict()
        assert d["results"] == {}

    def test_scheduled_at(self):
        fut = datetime.now() + timedelta(hours=1)
        task = PublishTask(
            id="1", title="T", content="C", platforms=[PlatformType.WECHAT_MP],
            scheduled_at=fut,
        )
        assert task.scheduled_at is not None

    def test_results_with_error(self):
        task = PublishTask(
            id="1", title="T", content="C", platforms=[PlatformType.WECHAT_MP],
            results={
                PlatformType.WECHAT_MP: PublishResult(
                    success=False, platform="wechat_mp", error="API rate limited"
                ),
            },
        )
        d = task.to_dict()
        assert d["results"]["wechat_mp"]["success"] is False
        assert d["results"]["wechat_mp"]["error"] == "API rate limited"

    def test_max_retries_override(self):
        task = PublishTask(id="1", title="T", content="C", platforms=[PlatformType.WECHAT_MP], max_retries=5)
        assert task.max_retries == 5


class TestPlatformAccount:
    def test_default_values(self):
        acc = PlatformAccount(id="acc-1", platform=PlatformType.WECHAT_MP, name="My Account", config={"appid": "wx..."})
        assert acc.id == "acc-1"
        assert acc.platform == PlatformType.WECHAT_MP
        assert acc.name == "My Account"
        assert acc.config == {"appid": "wx..."}
        assert acc.is_active is True
        assert acc.last_validated is None

    def test_inactive(self):
        acc = PlatformAccount(id="acc-2", platform=PlatformType.WECHAT_MP, name="Disabled", config={}, is_active=False)
        assert acc.is_active is False
