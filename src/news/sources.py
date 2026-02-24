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
        "VentureBeat AI", "https://venturebeat.com/category/ai/feed/", "news", 0.85
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
        "Google AI Blog", "https://blog.google/technology/ai/rss/", "blog", 0.75
    ),
    NewsSource("OpenAI Blog", "https://openai.com/blog/rss.xml", "blog", 0.9),
]
