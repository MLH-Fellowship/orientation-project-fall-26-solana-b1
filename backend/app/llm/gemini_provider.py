"""Google Gemini implementation of LLMProvider.

Uses the free-tier-eligible Gemini API. Get a key at
https://aistudio.google.com/apikey
"""

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

    def generate_title(self, user_message: str, assistant_message: str) -> str:
        prompt = (
            "Generate a short conversation title of 3–6 words based on the exchange below. "
            "Reply with ONLY the title, no quotes or punctuation.\n\n"
            f"User: {user_message}\nAssistant: {assistant_message}"
        )
        contents = [
            types.Content(role="user", parts=[types.Part(text=prompt)])
        ]
        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
        )
        return response.text
