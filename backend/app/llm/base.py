"""
Abstract interface for LLM providers.

Barebones ships with one implementation (Gemini). Fellows will add
more providers (OpenAI, local/Ollama, etc.) behind this same interface
-- see ISSUES.md, "LLM Integration" section.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass
class LLMReply:
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class LLMProvider(ABC):
    @abstractmethod
    def generate_reply(self, history: list[dict[str, str]]) -> LLMReply:
        """
        Given conversation history as a list of {"role": ..., "content": ...}
        dicts, return the assistant's text and token counts.
        """
        raise NotImplementedError

    def generate_reply_stream(self, history: list[dict[str, str]]) -> Iterator[str]:
        """Yield assistant response text chunks in generation order."""
        yield self.generate_reply(history).text

    @abstractmethod
    def generate_title(self, user_message: str, assistant_message: str) -> str:
        """
        Given the first user message and the assistant's reply, return a
        short (3–6 word) conversation title.
        """
        raise NotImplementedError
