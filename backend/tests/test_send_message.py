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
