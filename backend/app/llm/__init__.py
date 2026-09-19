from app.config import settings
from app.llm.base import LLMProvider
from app.llm.gemini_provider import GeminiProvider


def get_llm_provider() -> LLMProvider:
    """Factory: returns the configured LLM provider. Extend with more
    branches as new providers are added (see ISSUES.md)."""
    if settings.llm_provider == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
