import logging

import feedparser
import httpx

from src.models import NewsItem
from src.news.sources import NewsSource

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 10.0


def fetch_feed(source: NewsSource) -> list[NewsItem]:
    try:
        response = httpx.get(source.url, timeout=HTTP_TIMEOUT, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("Failed to fetch %s: %s", source.name, e)
        return []

    feed = feedparser.parse(response.text)
    if feed.bozo and not feed.entries:
        logger.warning("Malformed feed from %s: %s", source.name, feed.bozo_exception)
        return []

    items: list[NewsItem] = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()
        if not title or not url:
            continue
        items.append(
            NewsItem(
                title=title,
                url=url,
                summary=entry.get("summary", "")[:500],
                published=entry.get("published", ""),
                source=source.name,
            )
        )

    logger.info("Fetched %d items from %s", len(items), source.name)
    return items


def fetch_all_feeds(sources: list[NewsSource]) -> list[NewsItem]:
    all_items: list[NewsItem] = []
    for source in sources:
        all_items.extend(fetch_feed(source))
    return all_items
