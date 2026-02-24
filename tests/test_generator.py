import json
from pathlib import Path
from unittest.mock import patch

from src.generation.generator import _parse_response, generate_tweets
from src.models import NewsItem, TweetStatus

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_RESPONSE = (FIXTURES_DIR / "sample_gemini_response.json").read_text()


def _make_item(title: str = "Test Article") -> NewsItem:
    return NewsItem(
        title=title,
        url="https://example.com/test",
        summary="Test summary",
        published="Mon, 24 Feb 2026 10:00:00 GMT",
        source="Test Source",
    )


class TestParseResponse:
    def test_parses_clean_json(self) -> None:
        drafts = _parse_response(SAMPLE_RESPONSE)
        assert len(drafts) == 2
        assert drafts[0].news_url == "https://example.com/gpt5-release"
        assert drafts[0].status == TweetStatus.PENDING
        assert drafts[0].created_at != ""

    def test_strips_markdown_fences(self) -> None:
        wrapped = f"```json\n{SAMPLE_RESPONSE}\n```"
        drafts = _parse_response(wrapped)
        assert len(drafts) == 2

    def test_raises_on_invalid_json(self) -> None:
        try:
            _parse_response("not json at all")
            assert False, "Should have raised"
        except json.JSONDecodeError:
            pass

    def test_raises_on_missing_keys(self) -> None:
        incomplete = json.dumps([{"news_url": "https://a.com"}])
        try:
            _parse_response(incomplete)
            assert False, "Should have raised"
        except KeyError:
            pass


class TestGenerateTweets:
    def test_returns_empty_for_no_items(self) -> None:
        result = generate_tweets([])
        assert result == []

    def test_successful_generation(self) -> None:
        with patch("src.generation.generator.generate_text", return_value=SAMPLE_RESPONSE):
            drafts = generate_tweets([_make_item()])
        assert len(drafts) == 2

    def test_retries_on_parse_failure(self) -> None:
        call_count = 0

        def mock_generate(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "invalid json"
            return SAMPLE_RESPONSE

        with patch("src.generation.generator.generate_text", side_effect=mock_generate):
            drafts = generate_tweets([_make_item()])
        assert len(drafts) == 2
        assert call_count == 2

    def test_returns_empty_after_max_retries(self) -> None:
        with patch("src.generation.generator.generate_text", return_value="broken"):
            drafts = generate_tweets([_make_item()])
        assert drafts == []
