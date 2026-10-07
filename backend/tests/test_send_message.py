from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Message
from app.routes import chat


class FailingProvider:
    def generate_reply(self, history):
        raise RuntimeError("LLM unavailable")


class StreamingProvider:
    def generate_reply_stream(self, history):
        yield "A streamed"
        yield " reply"


def test_failed_reply_does_not_save_user_message(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'chat.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autoflush=False, bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(chat, "get_llm_provider", FailingProvider)
    try:
        client = TestClient(app, raise_server_exceptions=False)
        convo = client.post("/api/conversations", json={"title": "Test"}).json()

        response = client.post(
            f"/api/conversations/{convo['id']}/messages", json={"content": "hello"}
        )

        assert response.status_code == 500
        with session_factory() as db:
            assert db.query(Message).count() == 0
    finally:
        app.dependency_overrides.clear()


def test_streamed_reply_is_forwarded_and_saved(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'chat.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autoflush=False, bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(chat, "get_llm_provider", StreamingProvider)
    try:
        client = TestClient(app)
        convo = client.post("/api/conversations", json={"title": "Test"}).json()

        response = client.post(
            f"/api/conversations/{convo['id']}/messages/stream", json={"content": "hello"}
        )

        events = [line for line in response.text.splitlines() if line]
        assert response.status_code == 200
        assert '"text": "A streamed"' in events[0]
        assert '"text": " reply"' in events[1]
        assert '"type": "done"' in events[2]
        with session_factory() as db:
            messages = db.query(Message).order_by(Message.created_at).all()
            assert [message.content for message in messages] == ["hello", "A streamed reply"]
    finally:
        app.dependency_overrides.clear()
