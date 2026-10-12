"""OpenAI implementation of LLMProvider."""

from openai import OpenAI

from app.config import settings
from app.llm.base import LLMProvider, LLMReply


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate_reply(self, history: list[dict]) -> LLMReply:
        messages = []

        # Prepend system prompt if configured
        if settings.system_prompt:
            messages.append({"role": "system", "content": settings.system_prompt})

        # Append incoming user/assistant message history
        for m in history:
            messages.append({"role": m["role"], "content": m["content"]})

        response = self.client.chat.completions.create(
            model=settings.openai_model, messages=messages
        )

        usage = response.usage
        return LLMReply(
            text=response.choices[0].message.content or "",
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
        )

    def generate_title(self, user_message: str, assistant_message: str) -> str:
        prompt = (
            "Generate a short conversation title of 3–6 words based on the exchange below. "
            "Reply with ONLY the title, no quotes or punctuation.\n\n"
            f"User: {user_message}\nAssistant: {assistant_message}"
        )
        messages = [{"role": "user", "content": prompt}]

        response = self.client.chat.completions.create(
            model=settings.openai_model, messages=messages
        )
        content = response.choices[0].message.content
        return content or "New Conversation"