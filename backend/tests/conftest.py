import os
from pathlib import Path

import pytest
import responses
from responses.registries import OrderedRegistry
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


os.environ.setdefault("JWT_SECRET", "integration-test-secret-at-least-32-characters")


@pytest.fixture
def gemini_http(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "test-api-key")
    monkeypatch.setattr(settings, "gemini_model", "gemini-test")
    monkeypatch.setattr(settings, "llm_provider", "gemini")
    monkeypatch.setattr(settings, "system_prompt", "")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "false")
    with responses.RequestsMock(registry=OrderedRegistry) as interceptor:
        yield interceptor


@pytest.fixture
def gemini_response(gemini_http):
    """Supply JSON at the HTTP boundary. Keep the Gemini SDK in use."""

    def register(text="A test reply", usage=None):
        payload = {
            "candidates": [
                {"content": {"role": "model", "parts": [{"text": text}]}, "finishReason": "STOP"}
            ]
        }
        if usage is not None:
            payload["usageMetadata"] = usage
        return gemini_http.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent",
            json=payload,
        )

    return register


@pytest.fixture
def migrated_api(tmp_path):
    from app.database import create_database_engine, get_db
    from app.main import app

    database_url = f"sqlite:///{tmp_path / 'api.db'}"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    engine = create_database_engine(database_url)
    sessions = sessionmaker(autoflush=False, bind=engine)

    def override_db():
        with sessions() as session:
            yield session

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client, sessions
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        engine.dispose()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from app.rate_limit import limiter

    limiter.reset()
    yield
    limiter.reset()


class FakeProvider:
    """Stands in for an LLMProvider so tests never call a real API."""

    def generate_reply(self, history: list[dict]):
        from app.llm.base import LLMReply

        return LLMReply(text=f"echo: {history[-1]['content']}")

    def generate_title(self, user_message: str, assistant_message: str) -> str:
        return "Test title"


@pytest.fixture
def client(monkeypatch):
    """TestClient backed by a temporary in-memory SQLite DB and a fake LLM."""
    from app.database import Base, get_db
    from app.main import app
    from app.routes import chat

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(chat, "get_llm_provider", lambda: FakeProvider())
    yield TestClient(app)
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)
