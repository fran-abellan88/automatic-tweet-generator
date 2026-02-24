import json
import logging
import re
from datetime import datetime, timezone

from src.generation.gemini_client import generate_text
from src.generation.prompt_builder import build_prompt
from src.models import NewsItem, TweetDraft

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


def generate_tweets(news_items: list[NewsItem]) -> list[TweetDraft]:
    if not news_items:
        logger.info("No news items to generate tweets for")
        return []

    prompt = build_prompt(news_items)

    for attempt in range(MAX_RETRIES):
        try:
            raw = generate_text(prompt)
            drafts = _parse_response(raw)
            logger.info("Generated %d tweet drafts", len(drafts))
            return drafts
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Failed to parse Gemini response (attempt %d): %s", attempt + 1, e)
            if attempt == 0:
                prompt = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON. No markdown fences or explanation."

    logger.error("Failed to generate tweets after %d attempts", MAX_RETRIES)
    return []


def _parse_response(raw: str) -> list[TweetDraft]:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    items = json.loads(cleaned)
    now = datetime.now(timezone.utc).isoformat()

    drafts: list[TweetDraft] = []
    for item in items:
        drafts.append(
            TweetDraft(
                news_url=item["news_url"],
                news_title=item["news_title"],
                tweet_text=item["tweet_text"],
                created_at=now,
            )
        )
    return drafts
