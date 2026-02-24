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
| TechCrunch AI | 0.85 |
| VentureBeat AI | 0.85 |
| ArXiv CS.AI+CS.LG | 0.80 |
| The Verge AI | 0.80 |
| Google AI Blog | 0.75 |
| Hugging Face Blog | 0.70 |
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

**Current boost keywords:** `gpt`, `claude`, `gemini`, `llama`, `mistral`, `open source`, `benchmark`, `sota`, `release`, `launch`, `announcement`, `breakthrough`, `transformer`, `diffusion`, `agent`, `rag`, `fine-tuning`, `reasoning`

---

## Score range

| Scenario | Calculation | Score |
|---|---|---|
| Maximum possible | 0.90 × 1.0 × 1.5 | **1.35** |
| Lowest publishable | 0.70 × 0.5 × 1.0 | **0.35** |
| Article older than 48h | any × 0.0 × any | **0.0** (discarded) |

The top `MAX_DRAFTS_PER_RUN = 3` items by score are sent to Gemini for tweet generation. The `source_score` value shown in the Telegram draft message is this final score.
