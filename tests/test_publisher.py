from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.twitter.publisher import publish_tweet


class TestPublishTweet:
    def test_publishes_and_returns_id(self) -> None:
        mock_client = MagicMock()
        mock_client.create_tweet.return_value = SimpleNamespace(data={"id": "12345"})

        with patch("src.twitter.publisher._get_client", return_value=mock_client):
            tweet_id = publish_tweet("Hello world! #AI")

        assert tweet_id == "12345"
        mock_client.create_tweet.assert_called_once_with(text="Hello world! #AI")

    def test_passes_full_text(self) -> None:
        mock_client = MagicMock()
        mock_client.create_tweet.return_value = SimpleNamespace(data={"id": "99"})

        long_text = "A" * 270 + " #AI #ML"
        with patch("src.twitter.publisher._get_client", return_value=mock_client):
            publish_tweet(long_text)

        mock_client.create_tweet.assert_called_once_with(text=long_text)
