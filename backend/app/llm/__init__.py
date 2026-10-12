from app.config import settings
from app.llm.base import LLMProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.openai_provider import OpenAIProvider


def get_llm_provider() -> LLMProvider:
    """Factory: returns the configured LLM provider. Extend with more
    branches as new providers are added (see ISSUES.md)."""

    provider = settings.llm_provider.lower()
    if provider == "gemini":
        return GeminiProvider()
    elif provider == "openai":
        return OpenAIProvider()

    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
