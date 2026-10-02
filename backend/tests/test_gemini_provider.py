from unittest.mock import Mock

import pytest

from app.config import settings
from app.llm.gemini_provider import GeminiProvider


@pytest.mark.parametrize(
    ("system_prompt", "expected_instruction"),
    [
        ("", None),
        ("Answer as a Solana mentor.", "Answer as a Solana mentor."),
    ],
)
def test_generate_reply_passes_optional_system_prompt(
    monkeypatch, system_prompt, expected_instruction
):
    client = Mock()
    client.models.generate_content.return_value.text = "A test reply"
    monkeypatch.setattr("app.llm.gemini_provider.genai.Client", lambda **_: client)
    monkeypatch.setattr(settings, "system_prompt", system_prompt)

    provider = GeminiProvider()
    result = provider.generate_reply([{"role": "user", "content": "Hello"}])

    assert result == "A test reply"
    config = client.models.generate_content.call_args.kwargs["config"]
    if expected_instruction is None:
        assert config is None
    else:
        assert config.system_instruction == expected_instruction
