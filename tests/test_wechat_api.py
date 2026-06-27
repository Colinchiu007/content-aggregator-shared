"""Tests for WeChat API utility functions."""
import pytest
from content_aggregator_shared.shared.wechat_mp.publisher import DraftResult, ImagePostResult, html_to_plaintext
from content_aggregator_shared.shared.wechat_mp.crypto import CredentialCrypto


class TestWechatApiUtils:
    """Verify that static utilities and data classes work correctly."""

    def test_draft_result_str(self):
        r = DraftResult(media_id="test_media_id")
        assert "test_media_id" in str(r)

    def test_image_post_result_counts(self):
        r = ImagePostResult(media_id="m1", image_count=3)
        assert r.image_count == 3

    def test_html_to_plaintext_with_script_style(self):
        html = """<div>
            <script>console.log("test")</script>
            <p>Visible text</p>
            <style>.cls{color:red}</style>
        </div>"""
        result = html_to_plaintext(html)
        assert "Visible text" in result
        assert "console.log" not in result
        assert ".cls" not in result

    def test_html_to_plaintext_entity_decode(self):
        assert html_to_plaintext("&quot;quoted&quot;") == '"quoted"'
        assert html_to_plaintext("&apos;single&apos;") == "'single'"

    def test_html_to_plaintext_consecutive_breaks(self):
        html = "a<br><br><br>b"
        result = html_to_plaintext(html)
        assert "a" in result
        assert "b" in result
        # Multiple newlines should be collapsed
        assert "\n" in result
