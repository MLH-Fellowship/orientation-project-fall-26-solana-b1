from unittest.mock import Mock

from app.config import settings
from app.llm.gemini_provider import GeminiProvider


def test_generate_reply_includes_configured_system_prompt(monkeypatch):
    client = Mock()
    client.models.generate_content.return_value.text = "A test reply"
    monkeypatch.setattr("app.llm.gemini_provider.genai.Client", lambda **_: client)
    monkeypatch.setattr(settings, "system_prompt", "Answer as a Solana mentor.")

    provider = GeminiProvider()
    result = provider.generate_reply([{"role": "user", "content": "Hello"}])

    assert result == "A test reply"
    request = client.models.generate_content.call_args.kwargs
    assert request["config"].system_instruction == "Answer as a Solana mentor."


def test_generate_reply_omits_config_when_system_prompt_is_unset(monkeypatch):
    client = Mock()
    client.models.generate_content.return_value.text = "A test reply"
    monkeypatch.setattr("app.llm.gemini_provider.genai.Client", lambda **_: client)
    monkeypatch.setattr(settings, "system_prompt", None)

    provider = GeminiProvider()
    provider.generate_reply([{"role": "user", "content": "Hello"}])

    request = client.models.generate_content.call_args.kwargs
    assert "config" not in request
