# Automatic Tweet Generator

Scrapes AI/Data Science news from RSS feeds, generates tweet drafts via Gemini, sends them to Telegram for human approval, and publishes approved tweets to Twitter/X. Runs entirely on GitHub Actions with no external infrastructure.

## How it works

```
[GitHub Actions Cron]
        │
        ▼
  RSS Scraper → Ranker → Gemini → Telegram (draft for approval)
                                        │
                               ✅ reply to approve
                               ❌ reply to reject
                                        │
[GitHub Actions Cron] ──────────────────┘
        │
        ▼
  Poll Telegram → Twitter/X API (publish approved tweets)
```

Two scheduled workflows run automatically:
- **Generate** (`generate.yml`): daily at 11:00 and 19:00 CET — scrapes feeds, ranks items, generates drafts, sends to Telegram
- **Publish** (`publish.yml`): every 30 min between 11:00–22:00 CET — polls Telegram for replies, publishes approved drafts

State is persisted in `data/state.json`, committed back to the repo after each run.

## Setup

### Prerequisites

- Python 3.12+
- A virtual environment (recommended)

### Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure credentials

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:

| Variable | Used by | Description |
|---|---|---|
| `GEMINI_API_KEY` | generate | Google AI Studio API key |
| `TELEGRAM_BOT_TOKEN` | both | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | both | Your Telegram user or group ID |
| `TWITTER_CONSUMER_KEY` | publish | Twitter app consumer key |
| `TWITTER_CONSUMER_SECRET` | publish | Twitter app consumer secret |
| `TWITTER_ACCESS_TOKEN` | publish | Twitter access token |
| `TWITTER_ACCESS_TOKEN_SECRET` | publish | Twitter access token secret |

### GitHub Actions secrets

Add the same variables as repository secrets under **Settings → Secrets and variables → Actions**.

## Running locally

Both scripts check prerequisites (env vars, dependencies, state file) before running.

**Generate tweet drafts:**
```bash
bash scripts/generate.sh
```

After running, you will receive Telegram messages with draft tweets. Reply ✅ to approve or ❌ to reject each one.

You can restrict generation to specific sources using `--sources`:

```bash
# List all available source names
bash scripts/generate.sh --list-sources

# Use only selected sources (useful for testing)
bash scripts/generate.sh --sources "Claude Blog" "Anthropic News"
bash scripts/generate.sh --sources "Cursor Blog"
```

Source name matching is case-insensitive.

**Publish approved tweets:**
```bash
bash scripts/publish.sh
```

This polls Telegram for your replies and publishes any approved drafts to Twitter/X.

## News sources

Feeds are defined in [`src/news/sources.py`](src/news/sources.py). Each source has:
- A category (`arxiv` / `news` / `blog`) used for content diversity
- A weight (`0.0–1.0`) that influences scoring

The ranker selects the top-scored item per category per run. See [`docs/scoring.md`](docs/scoring.md) for details on the scoring formula.

## Project structure

```
src/
├── config.py               # Env vars, thresholds, constants
├── models.py               # Pydantic models (NewsItem, TweetDraft, AppState)
├── news/
│   ├── sources.py          # RSS source registry
│   ├── rss_parser.py       # Feed fetching with feedparser + httpx
│   └── ranker.py           # Scoring, deduplication, category-based selection
├── generation/
│   ├── gemini_client.py    # google-genai wrapper
│   ├── prompt_builder.py   # System prompt and per-item prompt construction
│   └── generator.py        # Orchestrator: news items → TweetDraft[]
├── telegram/
│   └── bot.py              # sendMessage (drafts) + getUpdates (approvals)
├── twitter/
│   └── publisher.py        # tweepy v2 Client.create_tweet
├── storage/
│   └── state.py            # JSON read/write for AppState
└── workflows/
    ├── generate.py         # Entry point: scrape → rank → generate → telegram → save
    └── publish.py          # Entry point: poll telegram → publish → save

scripts/
├── generate.sh             # Local generate workflow with prerequisite checks
└── publish.sh              # Local publish workflow with prerequisite checks

data/
└── state.json              # Seen URLs, pending drafts, published tweets, Telegram offset

docs/
└── scoring.md              # Scoring formula reference
```

## Running tests

```bash
pytest tests/ -v
```
