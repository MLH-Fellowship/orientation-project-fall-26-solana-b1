from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Message
from app.routes import chat


@pytest.fixture
def api(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)

    def override_db():
        with sessions() as session:
            yield session

    provider = Mock()
    provider.generate_reply.return_value = "Mock reply"
    factory = Mock(return_value=provider)
    monkeypatch.setattr(chat, "get_llm_provider", factory)
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            response = client.post("/api/conversations", json={"title": "Test"})
            assert response.status_code == 200
            yield client, response.json()["id"], sessions, factory, provider
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        engine.dispose()


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
    client, conversation_id, sessions, factory, _ = api
    response = client.post(f"/api/conversations/{conversation_id}/messages", json=payload)
    assert response.status_code == 422
    assert any(error["loc"] == ["body", "content"] for error in response.json()["detail"])
    factory.assert_not_called()
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
def test_valid_content_is_trimmed_saved_and_sent_to_llm(api, content, expected):
    client, conversation_id, sessions, _, provider = api
    response = client.post(
        f"/api/conversations/{conversation_id}/messages", json={"content": content}
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Mock reply"
    provider.generate_reply.assert_called_once_with([{"role": "user", "content": expected}])
    with sessions() as session:
        messages = session.query(Message).all()
        assert len(messages) == 2
        assert next(m.content for m in messages if m.role == "user") == expected
