from app.models import Message


def test_failed_reply_does_not_save_user_message(migrated_api, gemini_http):
    client, sessions = migrated_api
    gemini_http.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent",
        status=503,
        json={"error": {"code": 503, "message": "API unavailable", "status": "UNAVAILABLE"}},
    )
    convo = client.post("/api/conversations", json={"title": "Test"}).json()

    response = client.post(f"/api/conversations/{convo['id']}/messages", json={"content": "hello"})

    assert response.status_code == 500
    assert len(gemini_http.calls) == 1
    with sessions() as db:
        assert db.query(Message).count() == 0


class StreamingProvider:
    def generate_reply_stream(self, history):
        yield "A streamed"
        yield " reply"


def test_streamed_reply_is_forwarded_and_saved(client, monkeypatch):
    from app.routes import chat

    monkeypatch.setattr(chat, "get_llm_provider", StreamingProvider)
    convo = client.post("/api/conversations", json={"title": "Test"}).json()

    response = client.post(
        f"/api/conversations/{convo['id']}/messages/stream", json={"content": "hello"}
    )

    events = [line for line in response.text.splitlines() if line]
    assert response.status_code == 200
    assert '"text": "A streamed"' in events[0]
    assert '"text": " reply"' in events[1]
    assert '"type": "done"' in events[2]
    full = client.get(f"/api/conversations/{convo['id']}").json()
    assert [message["content"] for message in full["messages"]] == [
        "hello",
        "A streamed reply",
    ]
