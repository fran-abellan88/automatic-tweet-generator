import json
import logging
import re
from datetime import datetime, timezone

from src.generation.gemini_client import generate_text
from src.generation.prompt_builder import build_prompt, build_thread_prompt
from src.models import ContentCategory, NewsItem, TweetDraft, classify_content

logger = logging.getLogger(__name__)

MAX_RETRIES = 2

THREAD_CATEGORIES = {ContentCategory.RESEARCH}


def generate_tweets(news_items: list[NewsItem]) -> list[TweetDraft]:
    if not news_items:
        logger.info("No news items to generate tweets for")
        return []

    single_items = [
        i for i in news_items
        if classify_content(i.source, i.title) not in THREAD_CATEGORIES
    ]
    thread_items = [
        i for i in news_items
        if classify_content(i.source, i.title) in THREAD_CATEGORIES
    ]

    drafts: list[TweetDraft] = []
    if single_items:
        drafts.extend(_generate_single_tweets(single_items))
    for item in thread_items:
        draft = _generate_thread(item)
        if draft:
            drafts.append(draft)
    return drafts


def _generate_single_tweets(news_items: list[NewsItem]) -> list[TweetDraft]:
    prompt = build_prompt(news_items)

    for attempt in range(MAX_RETRIES):
        try:
            raw = generate_text(prompt)
            drafts = _parse_single_response(raw)
            logger.info("Generated %d single tweet drafts", len(drafts))
            return drafts
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(
                "Failed to parse Gemini response (attempt %d): %s", attempt + 1, e
            )
            if attempt == 0:
                prompt = (
                    f"{prompt}\n\n"
                    "IMPORTANT: Return ONLY valid JSON. No markdown fences or explanation."
                )

    logger.error("Failed to generate single tweets after %d attempts", MAX_RETRIES)
    return []


def _generate_thread(item: NewsItem) -> TweetDraft | None:
    prompt = build_thread_prompt(item)

    for attempt in range(MAX_RETRIES):
        try:
            raw = generate_text(prompt)
            draft = _parse_thread_response(raw)
            logger.info(
                "Generated thread draft (%d tweets): %s",
                len(draft.thread_tweets),
                item.title[:50],
            )
            return draft
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning(
                "Failed to parse thread response (attempt %d): %s", attempt + 1, e
            )
            if attempt == 0:
                prompt = (
                    f"{prompt}\n\n"
                    "IMPORTANT: Return ONLY valid JSON. No markdown fences or explanation."
                )

    logger.error("Failed to generate thread for: %s", item.title[:50])
    return None


def _parse_single_response(raw: str) -> list[TweetDraft]:
    cleaned = _strip_fences(raw)
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


def _parse_thread_response(raw: str) -> TweetDraft:
    cleaned = _strip_fences(raw)
    data = json.loads(cleaned)

    thread_tweets: list[str] = data["thread_tweets"]
    if len(thread_tweets) < 2:
        raise ValueError(
            f"Thread must have at least 2 tweets, got {len(thread_tweets)}"
        )

    now = datetime.now(timezone.utc).isoformat()
    return TweetDraft(
        news_url=data["news_url"],
        news_title=data["news_title"],
        tweet_text=thread_tweets[0],
        thread_tweets=thread_tweets,
        created_at=now,
    )


def _strip_fences(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned
