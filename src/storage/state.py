import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import MAX_PUBLISHED_HISTORY_DAYS, MAX_SEEN_URLS
from src.models import AppState, RunLog

logger = logging.getLogger(__name__)

STATE_FILE = Path("data/state.json")


def load_state() -> AppState:
    if not STATE_FILE.exists():
        logger.info("No state file found, starting fresh")
        return AppState()
    raw = json.loads(STATE_FILE.read_text())
    return AppState.model_validate(raw)


def save_state(state: AppState) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _prune_state(state)
    STATE_FILE.write_text(state.model_dump_json(indent=2))
    logger.info(
        "State saved: %d seen URLs, %d pending, %d published",
        len(state.seen_urls),
        len(state.pending_drafts),
        len(state.published_tweets),
    )


def _prune_state(state: AppState) -> None:
    if len(state.seen_urls) > MAX_SEEN_URLS:
        state.seen_urls = state.seen_urls[-MAX_SEEN_URLS:]

    cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_PUBLISHED_HISTORY_DAYS)).isoformat()
    state.published_tweets = [t for t in state.published_tweets if (t.published_at or "") >= cutoff]


RUNS_DIR = Path("data/runs")


def save_run_log(run_log: RunLog) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{run_log.timestamp.replace(':', '-')}.json"
    filepath = RUNS_DIR / filename
    filepath.write_text(run_log.model_dump_json(indent=2))
    logger.info("Run log saved: %s (%d candidates)", filepath, len(run_log.candidates))
    return filepath
