"""
Abstract interface for LLM providers.

Barebones ships with one implementation (Gemini). Fellows will add
more providers (OpenAI, local/Ollama, etc.) behind this same interface
-- see ISSUES.md, "LLM Integration" section.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator


class LLMProvider(ABC):
    @abstractmethod
    def generate_reply(self, history: list[dict[str, str]]) -> str:
        """
        Given conversation history as a list of {"role": ..., "content": ...}
        dicts, return the assistant's full text reply.
        """
        raise NotImplementedError

    def generate_reply_stream(self, history: list[dict[str, str]]) -> Iterator[str]:
        """Yield assistant response text chunks in generation order."""
        yield self.generate_reply(history)
