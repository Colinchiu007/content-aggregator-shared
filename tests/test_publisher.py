"""Tests for Publisher — DraftResult, ImagePostResult, html_to_plaintext."""
import pytest
from content_aggregator_shared.shared.wechat_mp.publisher import (
    DraftResult, ImagePostResult, html_to_plaintext,
)


class TestDraftResult:
    def test_create(self):
        r = DraftResult(media_id="abc123")
        assert r.media_id == "abc123"

    def test_repr(self):
        r = DraftResult(media_id="m1")
        assert "m1" in repr(r)


class TestImagePostResult:
    def test_create(self):
        r = ImagePostResult(media_id="img1", image_count=5)
        assert r.media_id == "img1"
        assert r.image_count == 5


class TestHtmlToPlaintext:
    def test_empty(self):
        assert html_to_plaintext("") == ""

    def test_no_html(self):
        assert html_to_plaintext("hello world") == "hello world"

    def test_strip_simple_tags(self):
        assert html_to_plaintext("<p>Hello</p>") == "Hello"

    def test_multiple_paragraphs(self):
        html = "<p>First</p><p>Second</p>"
        result = html_to_plaintext(html)
        assert "First" in result
        assert "Second" in result

    def test_br_as_newline(self):
        assert html_to_plaintext("Line1<br>Line2") == "Line1\nLine2"

    def test_headings(self):
        html = "<h1>Title</h1><p>Body</p>"
        result = html_to_plaintext(html)
        assert "Title" in result
        assert "Body" in result

    def test_script_removal(self):
        html = "<p>Hello</p><script>alert('xss')</script><p>World</p>"
        result = html_to_plaintext(html)
        assert "alert" not in result
        assert "Hello" in result
        assert "World" in result

    def test_style_removal(self):
        html = "<p>Hello</p><style>.cls{color:red}</style><p>World</p>"
        result = html_to_plaintext(html)
        assert ".cls" not in result
        assert "Hello" in result

    def test_html_entities(self):
        assert html_to_plaintext("&amp; &lt; &gt;") == "& < >"

    def test_nested_tags(self):
        assert html_to_plaintext("<div><p><b>Bold</b> text</p></div>") == "Bold text"

    def test_newline_collapse(self):
        result = html_to_plaintext("<p>A</p><p>B</p><p>C</p>")
        # Multiple newlines should be collapsed
        assert "\n\n\n" not in result

    def test_whitespace_collapse(self):
        assert html_to_plaintext("hello     world") == "hello world"

    def test_unicode(self):
        assert html_to_plaintext("<p>中文内容</p>") == "中文内容"

    def test_mixed_content(self):
        html = """
        <div class="article">
            <h1>标题</h1>
            <p>第一段内容</p>
            <script>var x=1;</script>
            <p>第二段 &amp; 内容</p>
        </div>
        """
        result = html_to_plaintext(html)
        assert "标题" in result
        assert "第一段内容" in result
        assert "第二段" in result
        assert "&" in result
        assert "var x=1" not in result
