# Automatic Tweet Generator & Publisher

## Context

Build a fully automated, free service that scrapes AI/Data Science news, generates engaging tweet drafts via Google Gemini, sends them to Telegram for human approval, and publishes approved tweets to Twitter/X. Runs entirely on GitHub Actions with no external infrastructure.

## Architecture Overview

```
[GitHub Actions Cron] → [RSS Scraper] → [Ranker/Filter] → [Gemini LLM] → [Telegram Bot]
                                                                               ↓
[GitHub Actions Cron] → [Poll Telegram approvals] → [Twitter/X API] → [Published Tweet]
```

**Two workflows:**
1. **Generate** (daily, weekdays 12:00 UTC): scrape → rank → generate → send drafts to Telegram
2. **Publish** (every 30 min): poll Telegram for ✅/❌ replies → publish approved tweets

**State persistence:** `data/state.json` committed back to repo after each run (cheapest "database" possible).

**Concurrency control:** Both workflows share `concurrency: group: state-update` to prevent race conditions on state file pushes.

## Project Structure

```
src/
├── config.py                    # Env vars, thresholds, constants
├── models.py                    # Pydantic: NewsItem, TweetDraft, TweetStatus, AppState
├── news/
│   ├── sources.py               # NewsSource registry (RSS URLs, weights)
│   ├── rss_parser.py            # feedparser + httpx fetch
│   └── ranker.py                # Scoring (source_weight × recency × keyword_boost), dedup
├── generation/
│   ├── gemini_client.py         # google-generativeai wrapper (gemini-2.5-flash)
│   ├── prompt_builder.py        # System prompt + news → structured prompt
│   └── generator.py             # Orchestrator: news → prompt → Gemini → TweetDraft[]
├── telegram/
│   └── bot.py                   # sendMessage (drafts) + getUpdates (approvals) via httpx
├── twitter/
│   └── publisher.py             # tweepy v2 Client.create_tweet
├── storage/
│   └── state.py                 # JSON read/write for AppState
└── workflows/
    ├── generate.py              # Entry point: scrape → rank → generate → telegram → save state
    └── publish.py               # Entry point: poll telegram → publish approved → save state

data/
└── state.json                   # Seen URLs, pending drafts, published tweets, telegram offset

tests/
├── conftest.py
├── fixtures/                    # Sample RSS XML, Gemini responses
├── test_rss_parser.py
├── test_ranker.py
├── test_prompt_builder.py
├── test_generator.py
├── test_telegram_bot.py
├── test_publisher.py
└── test_state.py

.github/workflows/
├── generate.yml                 # Cron weekdays 12:00 UTC + workflow_dispatch
└── publish.yml                  # Cron every 30 min + workflow_dispatch
```

## Key Design Decisions

### Telegram Approval Flow (no server needed)
- Drafts sent as regular Telegram messages via Bot API HTTP POST
- User replies to each draft with ✅ (approve) or ❌ (reject)
- Publish workflow polls `getUpdates` every 30 min, matches `reply_to_message_id` against pending drafts
- Up to ~30 min latency between approval and publishing — acceptable for 1-3 daily tweets

### News Sources (RSS-only for v1)
- ArXiv CS.AI+CS.LG, MIT Tech Review, TechCrunch AI, VentureBeat AI, The Verge AI
- Hugging Face Blog, Google AI Blog, OpenAI Blog, Papers With Code
- Each source has a weight (0.0-1.0) for ranking
- Skip Anthropic/Meta blogs (no public RSS) — add later if needed

### Content Ranking (simple, no ML)
- `score = source_weight × recency_score × keyword_boost`
- Recency: 1.0 (<12h), 0.8 (<24h), 0.5 (<48h), 0.0 (older)
- Keyword boost: 1.5x for high-signal terms (GPT, Claude, Llama, open source, SOTA, etc.)
- Dedup: URL exact match + title similarity via `difflib.SequenceMatcher` (threshold 0.8)

### Tweet Style
- Engaging, casual, conversational — like a tech-savvy friend
- Hooks: questions, hot takes, surprising facts
- 1-2 emojis, 2-3 hashtags, under 270 chars (room for URL)
- Variety: opinions, questions, announcements, teasers

## Dependencies

```
feedparser>=6.0        # RSS parsing
google-generativeai>=0.8  # Gemini API
httpx>=0.27            # HTTP client (Telegram API, RSS fetch)
pydantic>=2.0          # Data models + validation
tweepy>=4.14           # Twitter/X API v2

# Dev
pytest>=8.0
black>=24.0
flake8>=7.0
```

## GitHub Actions Secrets Required

- `GEMINI_API_KEY`
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
- `TWITTER_CONSUMER_KEY`, `TWITTER_CONSUMER_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET`

## Implementation Order

| # | What | Key files |
|---|------|-----------|
| 1 | Project setup | `pyproject.toml`, `requirements.txt`, `.gitignore`, `src/__init__.py` files |
| 2 | Data models | `src/models.py` |
| 3 | Config | `src/config.py` |
| 4 | State management + tests | `src/storage/state.py`, `tests/test_state.py` |
| 5 | RSS parser + tests | `src/news/rss_parser.py`, `src/news/sources.py`, `tests/test_rss_parser.py` |
| 6 | Ranker + tests | `src/news/ranker.py`, `tests/test_ranker.py` |
| 7 | Gemini client + prompt builder + tests | `src/generation/`, `tests/test_prompt_builder.py`, `tests/test_generator.py` |
| 8 | Telegram bot + tests | `src/telegram/bot.py`, `tests/test_telegram_bot.py` |
| 9 | Twitter publisher + tests | `src/twitter/publisher.py`, `tests/test_publisher.py` |
| 10 | Workflow orchestrators | `src/workflows/generate.py`, `src/workflows/publish.py` |
| 11 | GitHub Actions workflows | `.github/workflows/generate.yml`, `.github/workflows/publish.yml` |

## Pitfalls to Watch

- **Telegram offset tracking**: Must persist `last_update_id` in state or old messages get reprocessed every run
- **GitHub Actions cron imprecision**: Can be delayed 5-15 min during high load — fine for this use case
- **Gemini free tier limits**: ~1,500 req/day for flash model — we use <10/day, well within limits
- **State file conflicts**: Concurrency group prevents workflow-vs-workflow conflicts; avoid manual edits to `data/state.json` while workflows run
- **RSS URL validation**: Some blog RSS URLs may be incorrect or change — validate all URLs in step 5 before hardcoding
- **Twitter free tier**: ~500 posts/month (not 1,500) — still covers 1-3/day easily

## Verification Plan

1. **Unit tests**: Run `pytest tests/ -v` — all modules have tests with mocked external APIs
2. **Local dry run**: Run `python -m src.workflows.generate` with env vars set — verify drafts appear in Telegram
3. **Approval test**: Reply ✅ to a draft in Telegram, run `python -m src.workflows.publish` — verify tweet appears on Twitter
4. **GitHub Actions**: Push to repo, trigger `workflow_dispatch` manually for both workflows, check logs
5. **Linting**: `flake8 src/ tests/` and `black --check src/ tests/` pass clean
