import json

import pytest

from app.config import settings
from app.llm.gemini_provider import GeminiProvider


@pytest.mark.parametrize("system_prompt", ["", "Answer as a Solana mentor."])
def test_generate_reply_passes_optional_system_prompt(monkeypatch, system_prompt, gemini_response):
    route = gemini_response()
    monkeypatch.setattr(settings, "system_prompt", system_prompt)

    result = GeminiProvider().generate_reply([{"role": "user", "content": "Hello"}])

    assert result.text == "A test reply"
    assert route.call_count == 1
    body = json.loads(route.calls[0].request.body)
    assert body["contents"] == [{"role": "user", "parts": [{"text": "Hello"}]}]
    if system_prompt:
        assert body["systemInstruction"]["parts"] == [{"text": system_prompt}]
    else:
        assert "systemInstruction" not in body
