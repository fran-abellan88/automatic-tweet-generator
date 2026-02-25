# News Item Scoring

Each news item is scored before deciding which articles get turned into tweet drafts.

## Formula

```
score = source_weight × recency_score × keyword_boost
```

All three factors are multiplied together, so a score of `0.0` in any factor discards the item entirely.

---

## source_weight

Defined per source in [`src/news/sources.py`](../src/news/sources.py). Represents editorial quality and relevance.

| Source | Weight |
|---|---|
| MIT Tech Review | 0.90 |
| OpenAI Blog | 0.90 |
| Claude Blog | 0.90 |
| Anthropic News | 0.90 |
| TechCrunch AI | 0.85 |
| VentureBeat AI | 0.85 |
| ArXiv CS.AI+CS.LG | 0.80 |
| The Verge AI | 0.80 |
| Google DeepMind | 0.80 |
| MIT News AI | 0.80 |
| Google AI Blog | 0.75 |
| Microsoft AI Blog | 0.75 |
| Daily Dose of Data Science | 0.75 |
| Hugging Face Blog | 0.70 |
| Cursor Blog | 0.70 |
| Unknown source (fallback) | 0.50 |

---

## recency_score

Computed from the article's publish date in [`src/news/ranker.py`](../src/news/ranker.py). Controlled by `RECENCY_THRESHOLD_HOURS = 48` in [`src/config.py`](../src/config.py).

| Article age | Score |
|---|---|
| < 12 hours | 1.0 |
| 12–24 hours | 0.8 |
| 24–48 hours | 0.5 |
| > 48 hours | **0.0** — item discarded |
| Unknown date | 0.3 |

---

## keyword_boost

Applied if any of the following keywords appear (case-insensitive) in the article title. Configured in `BOOST_KEYWORDS` in [`src/config.py`](../src/config.py).

| Condition | Multiplier |
|---|---|
| Title contains a boost keyword | 1.5× |
| No keyword match | 1.0× |

**Current boost keywords:** `gpt`, `claude`, `claude code`, `opus`, `sonnet`, `codex`, `GLM`, `MiniMax`, `opencode`, `copilot`, `gemini`, `llama`, `mistral`, `open source`, `benchmark`, `sota`, `release`, `launch`, `announcement`, `breakthrough`, `transformer`, `diffusion`, `agent`, `rag`, `fine-tuning`, `reasoning`

---

## Score range

Scores are normalized to a **0–10 scale** using the theoretical maximum raw score (0.9 × 1.0 × 1.5 = 1.35):

```
final_score = round(raw_score / 1.35 × 10, 2)
```

| Scenario | Raw | Score (0–10) |
|---|---|---|
| Maximum possible | 0.90 × 1.0 × 1.5 = 1.35 | **10.0** |
| High-quality news, fresh, keyword | 0.85 × 1.0 × 1.5 = 1.275 | **9.44** |
| Typical news, 12–24h, no keyword | 0.85 × 0.8 × 1.0 = 0.68 | **5.04** |
| Lowest non-zero | 0.70 × 0.5 × 1.0 = 0.35 | **2.59** |
| Article older than 48h | any × 0.0 × any = 0 | **0.0** (discarded) |

The top item per source category (arxiv / news / blog) is selected per run. The `source_score` shown in the Telegram draft message is this 0–10 value.
