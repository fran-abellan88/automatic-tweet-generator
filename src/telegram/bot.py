import logging
from dataclasses import dataclass

import httpx

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.models import CATEGORY_EMOJI, TweetDraft

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}"
HTTP_TIMEOUT = 15.0

APPROVE_TOKENS = {"✅", "approve", "yes", "ok", "si", "sí"}
REJECT_TOKENS = {"❌", "reject", "no", "skip"}


@dataclass
class TelegramDecision:
    reply_to_message_id: int
    approved: bool
    update_id: int


def send_draft(draft: TweetDraft, token: str = "", chat_id: str = "") -> int:
    token = token or TELEGRAM_BOT_TOKEN
    chat_id = chat_id or TELEGRAM_CHAT_ID

    logger.info("Sending draft to Telegram")

    cat_emoji = CATEGORY_EMOJI.get(draft.category, "📰")
    cat_label = draft.category.value.upper()
    score_display = f"{draft.source_score:.2f}"

    text = (
        f"{cat_emoji} <b>{cat_label}</b> | Score: {score_display}\n\n"
        f"{_escape_html(draft.tweet_text)}\n\n"
        f"📰 {_escape_html(draft.news_title)}\n"
        f"🔗 {draft.news_url}\n\n"
        "<i>Reply ✅ to approve or ❌ to reject</i>"
    )

    url = f"{TELEGRAM_API.format(token=token)}/sendMessage"
    response = httpx.post(
        url,
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()

    message_id: int = response.json()["result"]["message_id"]
    logger.info(
        "Sent draft to Telegram (message_id=%d): %s", message_id, draft.news_title[:50]
    )
    return message_id


def check_approvals(
    last_update_id: int, token: str = "", chat_id: str = ""
) -> list[TelegramDecision]:
    token = token or TELEGRAM_BOT_TOKEN
    chat_id = chat_id or TELEGRAM_CHAT_ID

    url = f"{TELEGRAM_API.format(token=token)}/getUpdates"
    response = httpx.get(
        url,
        params={"offset": last_update_id + 1, "timeout": 5},
        timeout=HTTP_TIMEOUT + 5,
    )
    response.raise_for_status()

    updates = response.json().get("result", [])
    decisions: list[TelegramDecision] = []

    for update in updates:
        msg = update.get("message", {})
        if str(msg.get("chat", {}).get("id")) != str(chat_id):
            continue

        reply = msg.get("reply_to_message")
        text = msg.get("text", "").strip().lower()

        if not reply or not text:
            continue

        if text in APPROVE_TOKENS:
            approved = True
        elif text in REJECT_TOKENS:
            approved = False
        else:
            continue

        decisions.append(
            TelegramDecision(
                reply_to_message_id=reply["message_id"],
                approved=approved,
                update_id=update["update_id"],
            )
        )

    logger.info("Found %d decisions from %d updates", len(decisions), len(updates))
    return decisions


def send_notification(text: str, token: str = "", chat_id: str = "") -> None:
    token = token or TELEGRAM_BOT_TOKEN
    chat_id = chat_id or TELEGRAM_CHAT_ID

    url = f"{TELEGRAM_API.format(token=token)}/sendMessage"
    response = httpx.post(
        url,
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        timeout=HTTP_TIMEOUT,
    )
    print(
        f"DEBUG: Telegram response status={response.status_code}, body={response.text}"
    )
    logger.error(
        "Telegram response status=%d, body=%s", response.status_code, response.text
    )
    response.raise_for_status()


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
