from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class NewsItem(BaseModel):
    title: str
    url: str
    summary: str
    published: str
    source: str
    score: float = 0.0


class TweetStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class ContentCategory(str, Enum):
    RESEARCH = "research"
    NEWS = "news"
    RELEASE = "release"
    BLOG = "blog"


RELEASE_KEYWORDS = {
    "release",
    "launch",
    "announce",
    "announcing",
    "introduces",
    "unveiled",
    "open-source",
    "open source",
}

SOURCE_CATEGORY_MAP: dict[str, ContentCategory] = {
    "ArXiv CS.AI+CS.LG": ContentCategory.RESEARCH,
    "TechCrunch AI": ContentCategory.NEWS,
    "VentureBeat AI": ContentCategory.NEWS,
    "The Verge AI": ContentCategory.NEWS,
    "MIT Tech Review": ContentCategory.NEWS,
    "Hugging Face Blog": ContentCategory.BLOG,
    "Google AI Blog": ContentCategory.BLOG,
    "OpenAI Blog": ContentCategory.BLOG,
    "Microsoft AI Blog": ContentCategory.BLOG,
    "Google DeepMind": ContentCategory.BLOG,
    "MIT News AI": ContentCategory.NEWS,
    "Daily Dose of Data Science": ContentCategory.BLOG,
    "Cursor Blog": ContentCategory.BLOG,
    "Claude Blog": ContentCategory.BLOG,
    "Anthropic News": ContentCategory.NEWS,
}

CATEGORY_EMOJI: dict[ContentCategory, str] = {
    ContentCategory.RESEARCH: "🔬",
    ContentCategory.NEWS: "📰",
    ContentCategory.RELEASE: "🚀",
    ContentCategory.BLOG: "📝",
}


def classify_content(source: str, title: str) -> ContentCategory:
    title_lower = title.lower()
    if any(kw in title_lower for kw in RELEASE_KEYWORDS):
        return ContentCategory.RELEASE
    return SOURCE_CATEGORY_MAP.get(source, ContentCategory.NEWS)


class TweetDraft(BaseModel):
    news_url: str
    news_title: str
    tweet_text: str
    source_score: float = 0.0
    category: ContentCategory = ContentCategory.NEWS
    status: TweetStatus = TweetStatus.PENDING
    telegram_message_id: int | None = None
    created_at: str = ""
    published_at: str | None = None
    tweet_id: str | None = None

    def mark_approved(self) -> None:
        self.status = TweetStatus.APPROVED

    def mark_rejected(self) -> None:
        self.status = TweetStatus.REJECTED

    def mark_published(self, tweet_id: str) -> None:
        self.status = TweetStatus.PUBLISHED
        self.tweet_id = tweet_id
        self.published_at = datetime.now().isoformat()


class ScoredCandidate(BaseModel):
    title: str
    url: str
    source: str
    score: float
    selected: bool = False


class RunLog(BaseModel):
    timestamp: str
    total_fetched: int
    after_dedup: int
    candidates: list[ScoredCandidate]
    drafts_generated: int = 0


class AppState(BaseModel):
    seen_urls: list[str] = []
    pending_drafts: list[TweetDraft] = []
    published_tweets: list[TweetDraft] = []
    last_telegram_update_id: int = 0
