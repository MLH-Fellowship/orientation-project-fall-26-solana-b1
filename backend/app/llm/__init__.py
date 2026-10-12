from app.config import settings
from app.llm.base import LLMProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.openai_provider import OpenAIProvider


def get_llm_provider(provider: str = "gemini") -> LLMProvider:
    """Factory: returns the configured LLM provider. Extend with more
    branches as new providers are added (see ISSUES.md)."""

    provider = (provider or settings.llm_provider).lower()
    if provider == "gemini":
        return GeminiProvider()
    elif provider == "openai":
        return OpenAIProvider()

    raise ValueError(f"Unknown LLM provider: {provider}")
