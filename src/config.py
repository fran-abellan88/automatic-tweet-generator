import os

# API Keys (from environment variables / GitHub Secrets)
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")
TWITTER_CONSUMER_KEY: str = os.environ.get("TWITTER_CONSUMER_KEY", "")
TWITTER_CONSUMER_SECRET: str = os.environ.get("TWITTER_CONSUMER_SECRET", "")
TWITTER_ACCESS_TOKEN: str = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET: str = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")

# Gemini
GEMINI_MODEL: str = "gemini-2.5-flash"

# Tweet generation
MAX_DRAFTS_PER_RUN: int = 3
MAX_TWEET_LENGTH: int = 270

# News filtering
RECENCY_THRESHOLD_HOURS: int = 48
DEDUP_SIMILARITY_THRESHOLD: float = 0.8

# State management
MAX_SEEN_URLS: int = 1000
MAX_PUBLISHED_HISTORY_DAYS: int = 90

# Keywords that boost a news item's score
BOOST_KEYWORDS: list[str] = [
    "gpt",
    "claude",
    "gemini",
    "llama",
    "mistral",
    "open source",
    "benchmark",
    "sota",
    "release",
    "launch",
    "announcement",
    "breakthrough",
    "transformer",
    "diffusion",
    "agent",
    "rag",
    "fine-tuning",
    "reasoning",
]
