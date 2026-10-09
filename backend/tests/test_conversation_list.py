"""
Tests for GET /api/conversations pagination.
"""

from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Conversation


def make_client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'chat.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    sessions = sessionmaker(bind=engine)

    def override_db():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    return client, sessions


def seed_conversations(sessions):
    """
    Insert three conversations with deterministic created_at values:
      - c1: oldest  (t=1)
      - c2, c3: same timestamp (t=2), so id tie-break must order them
    Return them in insertion order so the caller knows their ids.
    """
    t_old = datetime(2026, 1, 1, 10, 0, 0)
    t_new = datetime(2026, 1, 2, 10, 0, 0)
    with sessions() as session:
        c1 = Conversation(title="Oldest", created_at=t_old)
        c2 = Conversation(title="Tied A", created_at=t_new)
        c3 = Conversation(title="Tied B", created_at=t_new)
        session.add_all([c1, c2, c3])
        session.flush()
        ids = (c1.id, c2.id, c3.id)
        session.commit()
    return ids


def test_default_page_returns_all_and_correct_envelope(tmp_path):
    client, sessions = make_client(tmp_path)
    try:
        c1_id, c2_id, c3_id = seed_conversations(sessions)

        resp = client.get("/api/conversations")
        assert resp.status_code == 200
        body = resp.json()

        # envelope fields present
        assert body["total"] == 3
        assert body["limit"] == 20
        assert body["offset"] == 0
        assert len(body["items"]) == 3

        # newest first; tied pair ordered id DESC
        returned_ids = [item["id"] for item in body["items"]]

        tied_ids_sorted = sorted([c2_id, c3_id], reverse=True)
        assert returned_ids == [*tied_ids_sorted, c1_id]

        # each item has expected fields
        for item in body["items"]:
            assert {"id", "title", "created_at"} <= set(item)
            assert "messages" not in item
    finally:
        app.dependency_overrides.clear()


def test_sub_page_returns_correct_slice_and_total(tmp_path):
    client, sessions = make_client(tmp_path)
    try:
        c1_id, c2_id, c3_id = seed_conversations(sessions)

        # fetch the middle item only
        resp = client.get("/api/conversations?limit=1&offset=1")
        assert resp.status_code == 200
        body = resp.json()

        assert body["total"] == 3
        assert body["limit"] == 1
        assert body["offset"] == 1
        assert len(body["items"]) == 1

        tied_ids_sorted = sorted([c2_id, c3_id], reverse=True)
        assert body["items"][0]["id"] == tied_ids_sorted[1]
    finally:
        app.dependency_overrides.clear()


def test_offset_past_end_returns_empty_items_with_real_total(tmp_path):
    client, sessions = make_client(tmp_path)
    try:
        seed_conversations(sessions)

        resp = client.get("/api/conversations?offset=100")
        assert resp.status_code == 200
        body = resp.json()

        assert body["total"] == 3
        assert body["items"] == []
    finally:
        app.dependency_overrides.clear()


def test_invalid_limit_returns_422(tmp_path):
    client, _ = make_client(tmp_path)
    try:
        resp = client.get("/api/conversations?limit=0")
        assert resp.status_code == 422
        body = resp.json()
        assert set(body) == {"error"}
        assert {"code", "message"}.issubset(body["error"])
    finally:
        app.dependency_overrides.clear()


def test_invalid_offset_returns_422(tmp_path):
    client, _ = make_client(tmp_path)
    try:
        resp = client.get("/api/conversations?offset=-1")
        assert resp.status_code == 422
        body = resp.json()
        assert set(body) == {"error"}
        assert {"code", "message"}.issubset(body["error"])
    finally:
        app.dependency_overrides.clear()
