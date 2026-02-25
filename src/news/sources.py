from dataclasses import dataclass


@dataclass(frozen=True)
class NewsSource:
    name: str
    url: str
    category: str  # "arxiv", "blog", "news"
    weight: float  # 0.0-1.0, higher = more important


SOURCES: list[NewsSource] = [
    NewsSource(
        "ArXiv CS.AI+CS.LG", "https://rss.arxiv.org/rss/cs.AI+cs.LG", "arxiv", 0.8
    ),
    NewsSource(
        "MIT Tech Review", "https://www.technologyreview.com/feed/", "news", 0.9
    ),
    NewsSource(
        "TechCrunch AI",
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "news",
        0.85,
    ),
    NewsSource(
        "VentureBeat AI", "https://venturebeat.com/category/ai/feed", "news", 0.85
    ),
    NewsSource(
        "The Verge AI",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "news",
        0.8,
    ),
    NewsSource(
        "Hugging Face Blog", "https://huggingface.co/blog/feed.xml", "blog", 0.7
    ),
    NewsSource(
        "Google AI Blog",
        "https://blog.google/innovation-and-ai/technology/ai/rss/",
        "blog",
        0.75,
    ),
    NewsSource("OpenAI Blog", "https://openai.com/news/rss.xml", "blog", 0.9),
    NewsSource(
        "Microsoft AI Blog",
        "https://www.microsoft.com/en-us/ai/blog/feed/",
        "blog",
        0.75,
    ),
    NewsSource("Google DeepMind", "https://deepmind.google/blog/rss.xml", "blog", 0.8),
    NewsSource(
        "MIT News AI",
        "https://news.mit.edu/topic/artificial-intelligence2/feed",
        "news",
        0.8,
    ),
    NewsSource(
        "Daily Dose of Data Science",
        "https://blog.dailydoseofds.com/feed",
        "blog",
        0.75,
    ),
]
