import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.llm.base import LLMProvider
from app.main import app
from app.routes import chat


class FakeProvider(LLMProvider):
    def generate_reply(self, history: list[dict]) -> str:
        return f"echo: {history[-1]['content']}"


@pytest.fixture
def client(monkeypatch):
    """TestClient backed by a temporary in-memory SQLite DB and a fake LLM."""
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

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(chat, "get_llm_provider", lambda: FakeProvider())
    yield TestClient(app)
    app.dependency_overrides.clear()
