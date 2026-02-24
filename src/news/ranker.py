import logging
from datetime import datetime, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime

from src.config import BOOST_KEYWORDS, DEDUP_SIMILARITY_THRESHOLD, RECENCY_THRESHOLD_HOURS
from src.models import NewsItem
from src.news.sources import NewsSource

logger = logging.getLogger(__name__)


def score_item(item: NewsItem, source_weight: float) -> float:
    recency = _recency_score(item.published)
    keyword = _keyword_boost(item.title)
    return source_weight * recency * keyword


def _recency_score(published: str) -> float:
    if not published:
        return 0.3  # Unknown date gets a low but non-zero score

    try:
        pub_dt = parsedate_to_datetime(published)
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return 0.3

    age_hours = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600

    if age_hours < 12:
        return 1.0
    elif age_hours < 24:
        return 0.8
    elif age_hours < RECENCY_THRESHOLD_HOURS:
        return 0.5
    return 0.0


def _keyword_boost(title: str) -> float:
    title_lower = title.lower()
    for keyword in BOOST_KEYWORDS:
        if keyword in title_lower:
            return 1.5
    return 1.0


def deduplicate(items: list[NewsItem], seen_urls: list[str]) -> list[NewsItem]:
    unique: list[NewsItem] = []
    seen_titles: list[str] = []

    for item in items:
        if item.url in seen_urls:
            continue

        is_duplicate = False
        for title in seen_titles:
            if SequenceMatcher(None, item.title.lower(), title.lower()).ratio() > DEDUP_SIMILARITY_THRESHOLD:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(item)
            seen_titles.append(item.title)

    return unique


def rank_and_filter(
    items: list[NewsItem],
    sources: list[NewsSource],
    seen_urls: list[str],
    max_items: int = 5,
) -> list[NewsItem]:
    source_weights = {s.name: s.weight for s in sources}

    for item in items:
        weight = source_weights.get(item.source, 0.5)
        item.score = score_item(item, weight)

    filtered = [item for item in items if item.score > 0.0]
    deduped = deduplicate(filtered, seen_urls)
    ranked = sorted(deduped, key=lambda x: x.score, reverse=True)

    logger.info("Ranked %d items from %d total (after dedup from %d)", len(ranked[:max_items]), len(ranked), len(items))
    return ranked[:max_items]
