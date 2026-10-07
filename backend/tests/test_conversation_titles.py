"""
Tests for auto-generated conversation titles.

Uses an in-memory SQLite DB and a fake LLM provider.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.llm.base import LLMProvider
from app.main import app
from app.utils.titles import DEFAULT_TITLE


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class FakeLLMProvider(LLMProvider):
    title_side_effect = None
    title_return = "Test Generated Title"

    def generate_reply(self, history):
        return "This is a canned reply."

    def generate_title(self, user_message, assistant_message):
        if self.title_side_effect is not None:
            raise self.title_side_effect
        return self.title_return


def fake_llm_provider():
    return FakeLLMProvider()


@pytest.fixture(autouse=True)
def setup_overrides():
    """Swap real DB and LLM with test doubles for every test."""
    app.dependency_overrides[get_db] = override_get_db
    import app.routes.chat as chat_module

    original_get_llm = chat_module.get_llm_provider
    chat_module.get_llm_provider = fake_llm_provider

    FakeLLMProvider.title_side_effect = None
    FakeLLMProvider.title_return = "Test Generated Title"

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    app.dependency_overrides.pop(get_db, None)
    chat_module.get_llm_provider = original_get_llm


@pytest.fixture
def client():
    return TestClient(app)


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


def test_first_message_sets_llm_title(client):
    """Happy path: LLM title is persisted after the first exchange."""
    convo = create_conversation(client)
    send_message(client, convo["id"])
    assert get_title(client, convo["id"]) == "Test Generated Title"


def test_title_unchanged_after_second_message(client):
    """Title is only generated once; subsequent messages must not overwrite it."""
    convo = create_conversation(client)
    send_message(client, convo["id"], "First message")
    FakeLLMProvider.title_return = "Should Not Appear"
    send_message(client, convo["id"], "Second message")
    assert get_title(client, convo["id"]) == "Test Generated Title"


def test_llm_failure_falls_back_to_user_message(client):
    """When LLM raises, the title falls back to the (truncated) user message."""
    FakeLLMProvider.title_side_effect = RuntimeError("API down")
    convo = create_conversation(client)
    send_message(client, convo["id"], "Tell me about Python")
    title = get_title(client, convo["id"])
    assert title != DEFAULT_TITLE
    assert "Tell me about Python" in title or title.endswith("…")


def test_empty_llm_title_falls_back_to_user_message(client):
    """When LLM returns empty/unusable text, fallback applies (not DEFAULT_TITLE)."""
    FakeLLMProvider.title_return = '""'
    convo = create_conversation(client)
    send_message(client, convo["id"], "Short question")
    assert get_title(client, convo["id"]) == "Short question"


def test_custom_title_not_overwritten(client):
    """A title set at conversation creation must survive the first message."""
    convo = create_conversation(client, title="My Custom Title")
    send_message(client, convo["id"])
    assert get_title(client, convo["id"]) == "My Custom Title"
