# Plan: Thread Generation

## Contexto

Los threads de Twitter/X tienen mayor alcance orgánico que los tweets sueltos — más señales de engagement, más superficie algorítmica, y más valor por lectura. El objetivo es generar threads automáticamente para contenido con suficiente profundidad (papers de ArXiv), manteniendo tweets sueltos para noticias y blogs donde la profundidad es menor.

## Alcance

- **Categoría RESEARCH** (ArXiv CS.AI+CS.LG) → thread de 4–5 tweets
- **NEWS / BLOG / RELEASE** → tweet suelto (sin cambios)
- Compatibilidad total con `state.json` existente: los drafts actuales siguen funcionando

---

## Ficheros a modificar (6)

### 1. `src/models.py`

Añadir `thread_tweets: list[str] = []` y propiedad `is_thread` a `TweetDraft`.

- Para thread drafts: `tweet_text = thread_tweets[0]` (hook) — los consumidores existentes
  (notificación de publicación, cabecera Telegram) siguen funcionando sin cambios
- `is_thread`: `return len(self.thread_tweets) > 1`
- `tweet_text` pasa a tener default `""` para soportar drafts de thread
- Backward compat: Pydantic rellena `thread_tweets = []` en drafts antiguos del state.json

```python
class TweetDraft(BaseModel):
    ...
    tweet_text: str = ""
    thread_tweets: list[str] = []  # non-empty → thread

    @property
    def is_thread(self) -> bool:
        return len(self.thread_tweets) > 1
```

### 2. `src/generation/prompt_builder.py`

Añadir `build_thread_prompt(item: NewsItem) -> str` junto al `build_prompt()` existente.

Reglas del prompt de thread:
- Misma voz que tweets sueltos (informado, seco, sin hype)
- 4–5 tweets con estructura: Hook → Contexto → Hallazgo × 2 → Implicación
- Cada tweet ≤ 256 chars (URL se añade automáticamente al último tweet)
- Sin numeración "1/", sin marcadores "🧵" en el texto del tweet
- Prompt individual por item (no en batch), schema JSON:

```json
{"news_url": "...", "news_title": "...", "thread_tweets": ["tweet1", "tweet2", ...]}
```

### 3. `src/generation/generator.py`

Separar items por formato antes de llamar a Gemini:

```python
THREAD_CATEGORIES = {ContentCategory.RESEARCH}

def generate_tweets(news_items: list[NewsItem]) -> list[TweetDraft]:
    single_items = [i for i in news_items
                    if classify_content(i.source, i.title) not in THREAD_CATEGORIES]
    thread_items = [i for i in news_items
                    if classify_content(i.source, i.title) in THREAD_CATEGORIES]

    drafts: list[TweetDraft] = []
    if single_items:
        drafts.extend(_generate_single_tweets(single_items))  # lógica existente en batch
    for item in thread_items:
        draft = _generate_thread(item)                        # nueva llamada por item
        if draft:
            drafts.append(draft)
    return drafts
```

- `_generate_single_tweets()` extrae la lógica actual (sin cambios de comportamiento)
- `_generate_thread(item)` llama a `build_thread_prompt`, parsea `thread_tweets`,
  asigna `tweet_text = thread_tweets[0]`

### 4. `src/telegram/bot.py`

Actualizar `send_draft()` para mostrar preview del thread cuando `draft.is_thread`:

**Tweet suelto** → formato actual (sin cambios)

**Thread:**
```
🔬 RESEARCH | Score: 9.44 | 🧵 Thread (5 tweets)

[1/5] El hook del thread...

[2/5] Contexto del paper...

[3/5] Hallazgo clave uno...

[4/5] Hallazgo clave dos...

[5/5] Por qué importa para practitioners

📰 Título del paper
🔗 https://arxiv.org/...

Reply ✅ to approve or ❌ to reject
```

### 5. `src/twitter/publisher.py`

Añadir `publish_thread(tweets: list[str], url: str) -> str`:

```python
def publish_thread(tweets: list[str], url: str) -> str:
    client = _get_client()

    # Tweet 1: hook, sin URL
    resp = client.create_tweet(text=tweets[0])
    root_id = str(resp.data["id"])
    parent_id = root_id

    # Tweets intermedios: replies encadenados
    for tweet in tweets[1:-1]:
        resp = client.create_tweet(text=tweet, in_reply_to_tweet_id=parent_id)
        parent_id = str(resp.data["id"])

    # Último tweet: añadir URL
    last = build_tweet_text(tweets[-1], url)
    client.create_tweet(text=last, in_reply_to_tweet_id=parent_id)

    return root_id  # ID del tweet raíz, guardado en draft.tweet_id
```

### 6. `src/workflows/publish.py`

Importar `publish_thread` y ramificar en la línea donde se publica (actualmente línea 53):

```python
if draft.is_thread:
    tweet_id = publish_thread(draft.thread_tweets, draft.news_url)
else:
    tweet_id = publish_tweet(draft.tweet_text, draft.news_url)
```

---

## Riesgos conocidos

| Riesgo | Detalle |
|---|---|
| Coste API Twitter | Un thread de 5 tweets = 5 write ops. A 1 thread/día → ~150/mes + ~60 tweets sueltos = 210/mes. Límite: 500/mes. |
| Coste API Gemini | 1 llamada extra por item de ArXiv. Máx. 2/día → irrelevante frente a 1.500/día del tier gratuito. |
| Longitud Telegram | Preview de 5 tweets ≈ 1.200 chars. Límite Telegram: 4.096 chars. Sin problema. |
| Backward compat | `thread_tweets: list[str] = []` — Pydantic rellena el default en drafts existentes. Sin migración. |

---

## Verificación

1. `pytest tests/ -v` — tests existentes pasan sin regresiones
2. `bash scripts/generate.sh --sources "ArXiv CS.AI+CS.LG"` → Telegram muestra preview con
   formato `[1/N] ... [N/N]`
3. Reply ✅ en Telegram → `bash scripts/publish.sh` → Twitter muestra thread encadenado
4. `bash scripts/generate.sh --sources "TechCrunch AI"` → Telegram muestra tweet suelto
   (sin cambios respecto al comportamiento actual)
5. Verificar `data/state.json` tras generate: draft de ArXiv tiene campo `thread_tweets`
   con array de strings populado
