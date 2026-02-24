from pathlib import Path
from unittest.mock import patch

import httpx

from src.news.rss_parser import fetch_all_feeds, fetch_feed
from src.news.sources import NewsSource

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_RSS = (FIXTURES_DIR / "sample_rss.xml").read_text()


def _make_source(name: str = "Test Source", weight: float = 0.8) -> NewsSource:
    return NewsSource(name=name, url="https://example.com/feed", category="news", weight=weight)


def _mock_response(text: str, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code=status_code, text=text, request=httpx.Request("GET", "https://example.com"))


class TestFetchFeed:
    def test_parses_valid_rss(self) -> None:
        source = _make_source()
        with patch("src.news.rss_parser.httpx.get", return_value=_mock_response(SAMPLE_RSS)):
            items = fetch_feed(source)
        assert len(items) == 3
        assert items[0].title == "New GPT-5 Model Released by OpenAI"
        assert items[0].url == "https://example.com/gpt5-release"
        assert items[0].source == "Test Source"
        assert "OpenAI" in items[0].summary

    def test_returns_empty_on_http_error(self) -> None:
        source = _make_source()
        with patch("src.news.rss_parser.httpx.get", side_effect=httpx.ConnectError("Connection refused")):
            items = fetch_feed(source)
        assert items == []

    def test_returns_empty_on_http_status_error(self) -> None:
        source = _make_source()
        response = _mock_response("Not Found", status_code=404)
        with patch("src.news.rss_parser.httpx.get", return_value=response):
            items = fetch_feed(source)
        assert items == []

    def test_skips_entries_without_title(self) -> None:
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
            <item><link>https://example.com/a</link></item>
            <item><title>Valid</title><link>https://example.com/b</link></item>
        </channel></rss>"""
        source = _make_source()
        with patch("src.news.rss_parser.httpx.get", return_value=_mock_response(xml)):
            items = fetch_feed(source)
        assert len(items) == 1
        assert items[0].title == "Valid"

    def test_truncates_long_summaries(self) -> None:
        long_desc = "A" * 1000
        xml = f"""<?xml version="1.0"?>
        <rss version="2.0"><channel>
            <item><title>Test</title><link>https://example.com/a</link>
            <description>{long_desc}</description></item>
        </channel></rss>"""
        source = _make_source()
        with patch("src.news.rss_parser.httpx.get", return_value=_mock_response(xml)):
            items = fetch_feed(source)
        assert len(items[0].summary) == 500


class TestFetchAllFeeds:
    def test_aggregates_from_multiple_sources(self) -> None:
        source_a = _make_source("Source A")
        source_b = _make_source("Source B")
        with patch("src.news.rss_parser.httpx.get", return_value=_mock_response(SAMPLE_RSS)):
            items = fetch_all_feeds([source_a, source_b])
        assert len(items) == 6
        sources = {item.source for item in items}
        assert sources == {"Source A", "Source B"}

    def test_continues_on_partial_failure(self) -> None:
        source_ok = NewsSource(name="OK", url="https://ok.com/feed", category="news", weight=0.8)
        source_fail = NewsSource(name="Fail", url="https://fail.com/feed", category="news", weight=0.8)

        def side_effect(url: str, **kwargs: object) -> httpx.Response:
            if url == source_fail.url:
                raise httpx.ConnectError("fail")
            return _mock_response(SAMPLE_RSS)

        with patch("src.news.rss_parser.httpx.get", side_effect=side_effect):
            items = fetch_all_feeds([source_ok, source_fail])
        assert len(items) == 3
        assert all(item.source == "OK" for item in items)
