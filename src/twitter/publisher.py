import logging

import tweepy

from src.config import (
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    TWITTER_CONSUMER_KEY,
    TWITTER_CONSUMER_SECRET,
)

logger = logging.getLogger(__name__)


def _get_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=TWITTER_CONSUMER_KEY,
        consumer_secret=TWITTER_CONSUMER_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
    )


# Twitter shortens all URLs to 23 chars via t.co
TCO_URL_LENGTH = 23


def build_tweet_text(tweet_body: str, url: str) -> str:
    max_body = 280 - TCO_URL_LENGTH - 1  # 1 for the space before URL
    if len(tweet_body) > max_body:
        tweet_body = tweet_body[: max_body - 1] + "…"
    return f"{tweet_body} {url}"


def publish_tweet(text: str, url: str) -> str:
    full_text = build_tweet_text(text, url)
    client = _get_client()
    response = client.create_tweet(text=full_text)
    tweet_id = str(response.data["id"])
    logger.info("Published tweet %s", tweet_id)
    return tweet_id
