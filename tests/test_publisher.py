from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.twitter.publisher import build_tweet_text, publish_tweet


class TestBuildTweetText:
    def test_appends_url(self) -> None:
        result = build_tweet_text("Hello world! #AI", "https://example.com/article")
        assert result == "Hello world! #AI https://example.com/article"

    def test_truncates_long_body(self) -> None:
        body = "A" * 260
        result = build_tweet_text(body, "https://example.com")
        # 280 - 23 (t.co) - 1 (space) = 256 max body
        assert len(result.split(" https://")[0]) <= 256
        assert result.endswith("https://example.com")
        assert "…" in result

    def test_short_body_untouched(self) -> None:
        body = "Short tweet #AI"
        result = build_tweet_text(body, "https://example.com")
        assert result == "Short tweet #AI https://example.com"


class TestPublishTweet:
    def test_publishes_with_url_and_returns_id(self) -> None:
        mock_client = MagicMock()
        mock_client.create_tweet.return_value = SimpleNamespace(data={"id": "12345"})

        with patch("src.twitter.publisher._get_client", return_value=mock_client):
            tweet_id = publish_tweet("Hello world! #AI", "https://example.com/article")

        assert tweet_id == "12345"
        call_text = mock_client.create_tweet.call_args.kwargs["text"]
        assert "https://example.com/article" in call_text
        assert "Hello world! #AI" in call_text
