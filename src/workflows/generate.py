import argparse
import logging
import sys
from datetime import datetime, timezone

from src.config import MAX_DRAFTS_PER_RUN
from src.generation.generator import generate_tweets
from src.models import RunLog, ScoredCandidate, classify_content
from src.news.ranker import rank_and_filter
from src.news.rss_parser import fetch_all_feeds
from src.news.sources import SOURCES, NewsSource
from src.storage.state import load_state, save_run_log, save_state
from src.telegram.bot import send_draft

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate tweet drafts from RSS feeds."
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        metavar="NAME",
        help=(
            "Restrict to specific source names, e.g. --sources 'Claude Blog' 'Anthropic News'. "
            "Use --list-sources to see all available names."
        ),
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="Print all available source names and exit.",
    )
    return parser.parse_args()


def _resolve_sources(names: list[str]) -> list[NewsSource]:
    requested = {n.lower() for n in names}
    matched = [s for s in SOURCES if s.name.lower() in requested]
    unknown = requested - {s.name.lower() for s in matched}
    if unknown:
        logger.warning("Unknown source names (ignored): %s", ", ".join(sorted(unknown)))
    if not matched:
        logger.error("No valid sources matched. Use --list-sources to see available names.")
        sys.exit(1)
    logger.info("Filtering to sources: %s", [s.name for s in matched])
    return matched


def run() -> None:
    args = _parse_args()

    if args.list_sources:
        print("Available sources:")
        for s in SOURCES:
            print(f"  {s.name!r}  [{s.category}, weight={s.weight}]")
        return

    active_sources = _resolve_sources(args.sources) if args.sources else list(SOURCES)

    logger.info("Starting tweet generation workflow")

    state = load_state()

    # 1. Scrape all RSS feeds
    all_items = fetch_all_feeds(active_sources)
    if not all_items:
        logger.warning("No news items fetched from any source")
        return

    # 2. Rank, filter, and deduplicate
    top_items = rank_and_filter(all_items, active_sources, state.seen_urls, max_items=MAX_DRAFTS_PER_RUN)
    if not top_items:
        logger.info("No new relevant items after filtering")
        return

    # 3. Build run log with all scored candidates
    selected_urls = {item.url for item in top_items}
    candidates = [
        ScoredCandidate(
            title=item.title,
            url=item.url,
            source=item.source,
            score=item.score,
            selected=item.url in selected_urls,
        )
        for item in sorted(all_items, key=lambda x: x.score, reverse=True)
        if item.score > 0.0
    ][:50]  # Keep top 50 for analysis without bloating the log

    now = datetime.now(timezone.utc).isoformat()
    run_log = RunLog(
        timestamp=now,
        total_fetched=len(all_items),
        after_dedup=len(candidates),
        candidates=candidates,
    )

    # 4. Generate tweet drafts via Gemini
    drafts = generate_tweets(top_items)
    if not drafts:
        logger.error("Tweet generation failed")
        sys.exit(1)

    run_log.drafts_generated = len(drafts)

    # 5. Enrich drafts with score and category from the source news items
    item_map = {item.url: item for item in top_items}
    for draft in drafts:
        source_item = item_map.get(draft.news_url)
        if source_item:
            draft.source_score = source_item.score
            draft.category = classify_content(source_item.source, source_item.title)

    # 6. Send drafts to Telegram and track them
    for draft in drafts:
        try:
            message_id = send_draft(draft)
            draft.telegram_message_id = message_id
            state.pending_drafts.append(draft)
        except Exception:
            logger.exception("Failed to send draft to Telegram: %s", draft.news_title)

    # 7. Update seen URLs
    new_urls = [item.url for item in top_items]
    state.seen_urls.extend(new_urls)

    # 8. Save state and run log
    save_state(state)
    save_run_log(run_log)
    logger.info("Generation workflow complete: %d drafts sent to Telegram", len(drafts))


if __name__ == "__main__":
    run()
