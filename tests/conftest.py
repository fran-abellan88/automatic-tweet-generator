import os

# Ensure tests don't accidentally use real API keys
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "test-chat-id")
os.environ.setdefault("TWITTER_CONSUMER_KEY", "test-ck")
os.environ.setdefault("TWITTER_CONSUMER_SECRET", "test-cs")
os.environ.setdefault("TWITTER_ACCESS_TOKEN", "test-at")
os.environ.setdefault("TWITTER_ACCESS_TOKEN_SECRET", "test-ats")
