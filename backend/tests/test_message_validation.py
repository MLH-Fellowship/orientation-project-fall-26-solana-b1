import json

import pytest
from app.models import Message


@pytest.fixture
def api(migrated_api, gemini_http):
    client, sessions = migrated_api
    response = client.post("/api/conversations", json={"title": "Test"})
    assert response.status_code == 200
    return client, response.json()["id"], sessions, gemini_http


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"content": None},
        {"content": 123},
        {"content": []},
        {"content": ""},
        {"content": " \t\n"},
        {"content": "\u2003\u00a0"},
        {"content": "x" * 10001},
    ],
)
def test_invalid_content_has_no_side_effects(api, payload):
    client, conversation_id, sessions, interceptor = api
    response = client.post(f"/api/conversations/{conversation_id}/messages", json=payload)
    assert response.status_code == 422
    assert any(error["loc"] == ["body", "content"] for error in response.json()["error"]["details"])
    assert len(interceptor.calls) == 0
    with sessions() as session:
        assert session.query(Message).count() == 0


@pytest.mark.parametrize(
    "content, expected",
    [
        ("x", "x"),
        (" \tHello  world\nsecond line\n", "Hello  world\nsecond line"),
        ("x" * 10000, "x" * 10000),
        ("  " + "x" * 10000 + "\n", "x" * 10000),
        ("  Hello 🌍  ", "Hello 🌍"),
    ],
)
def test_valid_content_is_trimmed_saved_and_sent_to_llm(api, content, expected, gemini_response):
    client, conversation_id, sessions, _ = api
    route = gemini_response()
    response = client.post(
        f"/api/conversations/{conversation_id}/messages", json={"content": content}
    )
    assert response.status_code == 200
    assert response.json()["content"] == "A test reply"
    assert route.call_count == 1
    assert json.loads(route.calls[0].request.body)["contents"] == [
        {"role": "user", "parts": [{"text": expected}]}
    ]
    with sessions() as session:
        messages = session.query(Message).all()
        assert len(messages) == 2
        assert next(m.content for m in messages if m.role == "user") == expected
