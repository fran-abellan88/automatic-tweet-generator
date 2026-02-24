from unittest.mock import patch

import httpx

from src.models import ContentCategory, TweetDraft
from src.telegram.bot import check_approvals, send_draft


def _mock_response(json_data: dict, status_code: int = 200) -> httpx.Response:
    import json

    return httpx.Response(
        status_code=status_code,
        json=json_data,
        request=httpx.Request("POST", "https://api.telegram.org"),
    )


def _make_draft(
    category: ContentCategory = ContentCategory.RESEARCH, score: float = 1.2,
) -> TweetDraft:
    return TweetDraft(
        news_url="https://example.com/article",
        news_title="Test Article Title",
        tweet_text="This is a test tweet about AI! #AI #ML",
        source_score=score,
        category=category,
        created_at="2026-02-24T10:00:00",
    )


class TestSendDraft:
    def test_sends_message_and_returns_id(self) -> None:
        response = _mock_response({"ok": True, "result": {"message_id": 42}})
        with patch("src.telegram.bot.httpx.post", return_value=response) as mock_post:
            msg_id = send_draft(_make_draft(), token="test-token", chat_id="123")

        assert msg_id == 42
        call_args = mock_post.call_args
        assert "test-token" in call_args.args[0]
        body = call_args.kwargs["json"]
        assert body["chat_id"] == "123"
        assert "RESEARCH" in body["text"]
        assert "1.20" in body["text"]
        assert body["parse_mode"] == "HTML"

    def test_raises_on_http_error(self) -> None:
        response = _mock_response({"ok": False}, status_code=400)
        with patch("src.telegram.bot.httpx.post", return_value=response):
            try:
                send_draft(_make_draft(), token="test", chat_id="123")
                assert False, "Should have raised"
            except httpx.HTTPStatusError:
                pass


class TestCheckApprovals:
    def _make_updates(self, text: str, reply_message_id: int = 10, chat_id: int = 123) -> dict:
        return {
            "ok": True,
            "result": [
                {
                    "update_id": 999,
                    "message": {
                        "chat": {"id": chat_id},
                        "text": text,
                        "reply_to_message": {"message_id": reply_message_id},
                    },
                }
            ],
        }

    def test_detects_approval(self) -> None:
        response = _mock_response(self._make_updates("✅"))
        with patch("src.telegram.bot.httpx.get", return_value=response):
            decisions = check_approvals(0, token="test", chat_id="123")
        assert len(decisions) == 1
        assert decisions[0].approved is True
        assert decisions[0].reply_to_message_id == 10

    def test_detects_text_approval(self) -> None:
        response = _mock_response(self._make_updates("approve"))
        with patch("src.telegram.bot.httpx.get", return_value=response):
            decisions = check_approvals(0, token="test", chat_id="123")
        assert len(decisions) == 1
        assert decisions[0].approved is True

    def test_detects_rejection(self) -> None:
        response = _mock_response(self._make_updates("❌"))
        with patch("src.telegram.bot.httpx.get", return_value=response):
            decisions = check_approvals(0, token="test", chat_id="123")
        assert len(decisions) == 1
        assert decisions[0].approved is False

    def test_ignores_non_reply_messages(self) -> None:
        data = {
            "ok": True,
            "result": [
                {"update_id": 999, "message": {"chat": {"id": 123}, "text": "✅"}},
            ],
        }
        response = _mock_response(data)
        with patch("src.telegram.bot.httpx.get", return_value=response):
            decisions = check_approvals(0, token="test", chat_id="123")
        assert len(decisions) == 0

    def test_ignores_wrong_chat(self) -> None:
        response = _mock_response(self._make_updates("✅", chat_id=999))
        with patch("src.telegram.bot.httpx.get", return_value=response):
            decisions = check_approvals(0, token="test", chat_id="123")
        assert len(decisions) == 0

    def test_ignores_unrecognized_text(self) -> None:
        response = _mock_response(self._make_updates("hello"))
        with patch("src.telegram.bot.httpx.get", return_value=response):
            decisions = check_approvals(0, token="test", chat_id="123")
        assert len(decisions) == 0

    def test_empty_updates(self) -> None:
        response = _mock_response({"ok": True, "result": []})
        with patch("src.telegram.bot.httpx.get", return_value=response):
            decisions = check_approvals(0, token="test", chat_id="123")
        assert len(decisions) == 0
