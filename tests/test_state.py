import json
from pathlib import Path
from unittest.mock import patch

from src.models import AppState, TweetDraft, TweetStatus
from src.storage.state import load_state, save_state


def test_load_state_missing_file(tmp_path: Path) -> None:
    fake_path = tmp_path / "missing.json"
    with patch("src.storage.state.STATE_FILE", fake_path):
        state = load_state()
    assert state == AppState()


def test_load_state_existing_file(tmp_path: Path) -> None:
    fake_path = tmp_path / "state.json"
    data = AppState(seen_urls=["https://example.com"], last_telegram_update_id=42)
    fake_path.write_text(data.model_dump_json())
    with patch("src.storage.state.STATE_FILE", fake_path):
        state = load_state()
    assert state.seen_urls == ["https://example.com"]
    assert state.last_telegram_update_id == 42


def test_save_state_creates_file(tmp_path: Path) -> None:
    fake_path = tmp_path / "data" / "state.json"
    state = AppState(seen_urls=["https://a.com", "https://b.com"])
    with patch("src.storage.state.STATE_FILE", fake_path):
        save_state(state)
    assert fake_path.exists()
    loaded = json.loads(fake_path.read_text())
    assert len(loaded["seen_urls"]) == 2


def test_save_state_prunes_seen_urls(tmp_path: Path) -> None:
    fake_path = tmp_path / "state.json"
    state = AppState(seen_urls=[f"https://example.com/{i}" for i in range(1500)])
    with (
        patch("src.storage.state.STATE_FILE", fake_path),
        patch("src.storage.state.MAX_SEEN_URLS", 100),
    ):
        save_state(state)
    loaded = json.loads(fake_path.read_text())
    assert len(loaded["seen_urls"]) == 100
    assert loaded["seen_urls"][0] == "https://example.com/1400"


def test_save_state_prunes_old_published(tmp_path: Path) -> None:
    fake_path = tmp_path / "state.json"
    old_tweet = TweetDraft(
        news_url="https://old.com",
        news_title="Old",
        tweet_text="old tweet",
        status=TweetStatus.PUBLISHED,
        published_at="2020-01-01T00:00:00",
    )
    recent_tweet = TweetDraft(
        news_url="https://new.com",
        news_title="New",
        tweet_text="new tweet",
        status=TweetStatus.PUBLISHED,
        published_at="2099-01-01T00:00:00",
    )
    state = AppState(published_tweets=[old_tweet, recent_tweet])
    with patch("src.storage.state.STATE_FILE", fake_path):
        save_state(state)
    loaded = json.loads(fake_path.read_text())
    assert len(loaded["published_tweets"]) == 1
    assert loaded["published_tweets"][0]["news_url"] == "https://new.com"


def test_roundtrip(tmp_path: Path) -> None:
    fake_path = tmp_path / "state.json"
    draft = TweetDraft(
        news_url="https://example.com/article",
        news_title="Test Article",
        tweet_text="Check this out!",
        telegram_message_id=123,
        created_at="2026-02-24T10:00:00",
    )
    original = AppState(
        seen_urls=["https://a.com"],
        pending_drafts=[draft],
        last_telegram_update_id=99,
    )
    with patch("src.storage.state.STATE_FILE", fake_path):
        save_state(original)
        loaded = load_state()
    assert loaded.seen_urls == original.seen_urls
    assert loaded.pending_drafts[0].tweet_text == "Check this out!"
    assert loaded.last_telegram_update_id == 99
