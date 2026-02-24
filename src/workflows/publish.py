import logging

from src.models import TweetStatus
from src.storage.state import load_state, save_state
from src.telegram.bot import check_approvals, send_notification
from src.twitter.publisher import publish_tweet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

MAX_PUBLISH_FAILURES = 3


def run() -> None:
    logger.info("Starting publish workflow")

    state = load_state()

    if not state.pending_drafts:
        logger.info("No pending drafts to process")
        return

    # 1. Check Telegram for approval/rejection decisions
    decisions = check_approvals(state.last_telegram_update_id)

    # Update the offset to the highest update_id we've seen
    if decisions:
        state.last_telegram_update_id = max(d.update_id for d in decisions)

    # 2. Map decisions to pending drafts by telegram_message_id
    decision_map = {d.reply_to_message_id: d.approved for d in decisions}

    for draft in state.pending_drafts:
        if draft.telegram_message_id not in decision_map:
            continue

        if decision_map[draft.telegram_message_id]:
            draft.mark_approved()
        else:
            draft.mark_rejected()
            logger.info("Draft rejected: %s", draft.news_title)

    # 3. Publish approved drafts
    published_count = 0
    for draft in state.pending_drafts:
        if draft.status != TweetStatus.APPROVED:
            continue

        try:
            tweet_id = publish_tweet(draft.tweet_text, draft.news_url)
            draft.mark_published(tweet_id)
            published_count += 1
            logger.info("Published tweet %s: %s", tweet_id, draft.news_title)

            send_notification(f"✅ Tweet published: {draft.tweet_text[:100]}...")
        except Exception:
            logger.exception("Failed to publish tweet: %s", draft.news_title)

    # 4. Move published/rejected drafts out of pending
    still_pending = [d for d in state.pending_drafts if d.status == TweetStatus.PENDING]
    completed = [d for d in state.pending_drafts if d.status in (TweetStatus.PUBLISHED, TweetStatus.REJECTED)]

    state.published_tweets.extend([d for d in completed if d.status == TweetStatus.PUBLISHED])
    state.pending_drafts = still_pending

    # 5. Save state
    save_state(state)
    logger.info("Publish workflow complete: %d published, %d still pending", published_count, len(still_pending))


if __name__ == "__main__":
    run()
