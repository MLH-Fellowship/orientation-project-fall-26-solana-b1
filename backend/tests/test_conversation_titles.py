"""Test title requests through the Gemini SDK and intercepted HTTP calls."""

import pytest

from app.utils.titles import DEFAULT_TITLE


@pytest.fixture
def client(migrated_api):
    return migrated_api[0]


def create_conversation(client, title=None):
    body = {"title": title} if title else {}
    resp = client.post("/api/conversations", json=body)
    assert resp.status_code == 200
    return resp.json()


def send_message(client, conversation_id, content="Hello"):
    resp = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": content},
    )
    assert resp.status_code == 200
    return resp.json()


def get_title(client, conversation_id):
    resp = client.get(f"/api/conversations/{conversation_id}")
    assert resp.status_code == 200
    return resp.json()["title"]


def test_first_message_sets_llm_title(client, gemini_response):
    gemini_response()
    gemini_response("Test Generated Title")
    convo = create_conversation(client)
    send_message(client, convo["id"])
    assert get_title(client, convo["id"]) == "Test Generated Title"


def test_title_unchanged_after_second_message(client, gemini_response, gemini_http):
    gemini_response()
    gemini_response("Test Generated Title")
    convo = create_conversation(client)
    send_message(client, convo["id"], "First message")
    gemini_response()
    send_message(client, convo["id"], "Second message")
    assert get_title(client, convo["id"]) == "Test Generated Title"
    assert len(gemini_http.calls) == 3


def test_llm_failure_falls_back_to_user_message(client, gemini_response, gemini_http):
    gemini_response()
    gemini_http.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent",
        status=503,
        json={"error": {"code": 503, "message": "API unavailable", "status": "UNAVAILABLE"}},
    )
    convo = create_conversation(client)
    send_message(client, convo["id"], "Tell me about Python")
    title = get_title(client, convo["id"])
    assert title != DEFAULT_TITLE
    assert "Tell me about Python" in title or title.endswith("…")


def test_empty_llm_title_falls_back_to_user_message(client, gemini_response):
    gemini_response()
    gemini_response('""')
    convo = create_conversation(client)
    send_message(client, convo["id"], "Short question")
    assert get_title(client, convo["id"]) == "Short question"


def test_custom_title_not_overwritten(client, gemini_response, gemini_http):
    gemini_response()
    convo = create_conversation(client, title="My Custom Title")
    send_message(client, convo["id"])
    assert get_title(client, convo["id"]) == "My Custom Title"
    assert len(gemini_http.calls) == 1
