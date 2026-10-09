import os
from pathlib import Path

import pytest
import responses
from responses.registries import OrderedRegistry
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

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
