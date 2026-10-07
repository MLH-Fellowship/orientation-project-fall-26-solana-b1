"""Google Gemini implementation of LLMProvider.

Uses the free-tier-eligible Gemini API. Get a key at
https://aistudio.google.com/apikey
"""

from collections.abc import Iterator

from google import genai
from google.genai import types

from app.config import settings
from app.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def generate_reply(self, history: list[dict]) -> str:
        # Gemini uses "model" instead of "assistant" for the assistant role,
        # and expects content as a list of Part objects rather than a plain string.
        contents = [
            types.Content(
                role="model" if m["role"] == "assistant" else "user",
                parts=[types.Part(text=m["content"])],
            )
            for m in history
        ]

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=(
                types.GenerateContentConfig(system_instruction=settings.system_prompt)
                if settings.system_prompt
                else None
            ),
        )
        return response.text

    def generate_reply_stream(self, history: list[dict]) -> Iterator[str]:
        contents = [
            types.Content(
                role="model" if m["role"] == "assistant" else "user",
                parts=[types.Part(text=m["content"])],
            )
            for m in history
        ]

        response = self.client.models.generate_content_stream(
            model=settings.gemini_model,
            contents=contents,
            config=(
                types.GenerateContentConfig(system_instruction=settings.system_prompt)
                if settings.system_prompt
                else None
            ),
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
