from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import patch

from src.models import NewsItem
from src.news.ranker import _keyword_boost, _recency_score, deduplicate, rank_and_filter, score_item
from src.news.sources import NewsSource


def _make_item(
    title: str = "Test Article",
    url: str = "https://example.com/test",
    hours_ago: float = 6.0,
    source: str = "Test Source",
) -> NewsItem:
    pub_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return NewsItem(
        title=title,
        url=url,
        summary="A test summary",
        published=format_datetime(pub_time),
        source=source,
    )


class TestRecencyScore:
    def test_very_recent(self) -> None:
        pub = format_datetime(datetime.now(timezone.utc) - timedelta(hours=2))
        assert _recency_score(pub) == 1.0

    def test_medium_recent(self) -> None:
        pub = format_datetime(datetime.now(timezone.utc) - timedelta(hours=18))
        assert _recency_score(pub) == 0.8

    def test_older(self) -> None:
        pub = format_datetime(datetime.now(timezone.utc) - timedelta(hours=30))
        assert _recency_score(pub) == 0.5

    def test_too_old(self) -> None:
        pub = format_datetime(datetime.now(timezone.utc) - timedelta(hours=72))
        assert _recency_score(pub) == 0.0

    def test_empty_string(self) -> None:
        assert _recency_score("") == 0.3

    def test_invalid_date(self) -> None:
        assert _recency_score("not-a-date") == 0.3


class TestKeywordBoost:
    def test_boosted_keyword(self) -> None:
        assert _keyword_boost("New GPT-5 Released") == 1.5

    def test_no_keyword(self) -> None:
        assert _keyword_boost("Weather Update for Today") == 1.0

    def test_case_insensitive(self) -> None:
        assert _keyword_boost("LLAMA 4 is here") == 1.5

    def test_partial_match(self) -> None:
        assert _keyword_boost("Open source model") == 1.5


class TestScoreItem:
    def test_high_score(self) -> None:
        item = _make_item(title="GPT-5 Release", hours_ago=2.0)
        score = score_item(item, source_weight=0.9)
        assert score == 0.9 * 1.0 * 1.5  # weight * recency * keyword

    def test_low_score(self) -> None:
        item = _make_item(title="Random tech news", hours_ago=30.0)
        score = score_item(item, source_weight=0.5)
        assert score == 0.5 * 0.5 * 1.0


class TestDeduplicate:
    def test_removes_seen_urls(self) -> None:
        items = [_make_item(url="https://a.com"), _make_item(url="https://b.com")]
        result = deduplicate(items, seen_urls=["https://a.com"])
        assert len(result) == 1
        assert result[0].url == "https://b.com"

    def test_removes_similar_titles(self) -> None:
        items = [
            _make_item(title="OpenAI releases GPT-5 model", url="https://a.com"),
            _make_item(title="OpenAI releases GPT-5 model today", url="https://b.com"),
        ]
        result = deduplicate(items, seen_urls=[])
        assert len(result) == 1

    def test_keeps_different_titles(self) -> None:
        items = [
            _make_item(title="GPT-5 Released by OpenAI", url="https://a.com"),
            _make_item(title="Meta launches Llama 4", url="https://b.com"),
        ]
        result = deduplicate(items, seen_urls=[])
        assert len(result) == 2


class TestRankAndFilter:
    def test_returns_top_items(self) -> None:
        sources = [NewsSource("S1", "url", "news", 0.9)]
        items = [
            _make_item(title="GPT news", hours_ago=2, source="S1", url="https://a.com"),
            _make_item(title="Random stuff", hours_ago=30, source="S1", url="https://b.com"),
            _make_item(title="Llama release", hours_ago=6, source="S1", url="https://c.com"),
        ]
        result = rank_and_filter(items, sources, seen_urls=[], max_items=2)
        assert len(result) == 2
        assert result[0].score >= result[1].score

    def test_excludes_zero_score(self) -> None:
        sources = [NewsSource("S1", "url", "news", 0.9)]
        items = [_make_item(title="Ancient news", hours_ago=100, source="S1")]
        result = rank_and_filter(items, sources, seen_urls=[], max_items=5)
        assert len(result) == 0

    def test_respects_seen_urls(self) -> None:
        sources = [NewsSource("S1", "url", "news", 0.9)]
        items = [_make_item(title="GPT news", hours_ago=2, source="S1", url="https://seen.com")]
        result = rank_and_filter(items, sources, seen_urls=["https://seen.com"], max_items=5)
        assert len(result) == 0
