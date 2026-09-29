import pytest


def make(client, title="Hello"):
    return client.post("/api/conversations", json={"title": title}).json()


def test_create_and_default_title(client):
    assert make(client)["title"] == "Hello"
    r = client.post("/api/conversations", json={})
    assert r.status_code == 200
    assert r.json()["title"] == "New Conversation"


def test_list_conversations(client):
    assert client.get("/api/conversations").json() == []
    make(client, "a")
    make(client, "b")
    assert len(client.get("/api/conversations").json()) == 2


def test_get_conversation_and_404(client):
    c = make(client)
    r = client.get(f"/api/conversations/{c['id']}")
    assert r.status_code == 200
    assert r.json()["messages"] == []
    assert client.get("/api/conversations/nope").status_code == 404


def test_send_message_uses_mocked_llm(client):
    c = make(client)
    r = client.post(f"/api/conversations/{c['id']}/messages", json={"content": "hi"})
    assert r.status_code == 200
    assert r.json()["role"] == "assistant"
    assert r.json()["content"] == "echo: hi"
    msgs = client.get(f"/api/conversations/{c['id']}").json()["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]


def test_send_message_404(client):
    r = client.post("/api/conversations/nope/messages", json={"content": "hi"})
    assert r.status_code == 404


def test_rename_conversation(client):
    c = make(client)
    r = client.patch(f"/api/conversations/{c['id']}", json={"title": "  New name  "})
    assert r.status_code == 200
    assert r.json()["title"] == "New name"
    assert client.get(f"/api/conversations/{c['id']}").json()["title"] == "New name"


@pytest.mark.parametrize("title", ["", "   ", "x" * 201])
def test_rename_validation(client, title):
    c = make(client)
    r = client.patch(f"/api/conversations/{c['id']}", json={"title": title})
    assert r.status_code == 422


def test_rename_404(client):
    assert client.patch("/api/conversations/nope", json={"title": "x"}).status_code == 404


def test_delete_conversation_cascades(client):
    c = make(client)
    client.post(f"/api/conversations/{c['id']}/messages", json={"content": "hi"})
    r = client.delete(f"/api/conversations/{c['id']}")
    assert r.status_code == 204
    assert r.content == b""
    assert client.get(f"/api/conversations/{c['id']}").status_code == 404
    from app.database import get_db
    from app.main import app
    from app.models import Message

    db = next(app.dependency_overrides[get_db]())
    assert db.query(Message).count() == 0


def test_delete_404(client):
    assert client.delete("/api/conversations/nope").status_code == 404
