import logging

from google import genai

from src.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)


def generate_text(prompt: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    logger.info("Gemini response received (%d chars)", len(response.text))
    return response.text
