from src.generation.prompt_builder import build_prompt
from src.models import NewsItem


def _make_item(title: str = "Test Article", source: str = "Test Source") -> NewsItem:
    return NewsItem(
        title=title,
        url="https://example.com/test",
        summary="A test summary about AI developments.",
        published="Mon, 24 Feb 2026 10:00:00 GMT",
        source=source,
    )


class TestBuildPrompt:
    def test_contains_system_instructions(self) -> None:
        prompt = build_prompt([_make_item()])
        assert "STRUCTURAL RULES" in prompt
        assert "JSON" in prompt
        assert "hashtags" in prompt

    def test_contains_news_items(self) -> None:
        items = [_make_item("GPT-5 Release", "TechCrunch"), _make_item("Llama 4", "VentureBeat")]
        prompt = build_prompt(items)
        assert "GPT-5 Release" in prompt
        assert "Llama 4" in prompt
        assert "[TechCrunch]" in prompt
        assert "[VentureBeat]" in prompt

    def test_contains_urls(self) -> None:
        prompt = build_prompt([_make_item()])
        assert "https://example.com/test" in prompt

    def test_truncates_long_summaries(self) -> None:
        item = _make_item()
        item.summary = "X" * 500
        prompt = build_prompt([item])
        # Summary should be truncated to 200 chars in the prompt
        assert "X" * 200 in prompt
        assert "X" * 201 not in prompt
