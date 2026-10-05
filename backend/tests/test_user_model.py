from pathlib import Path
from unittest.mock import Mock

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_db
from app.main import app
from app.routes import chat
from app.models import Conversation, Message, User


def migration_config(database_url):
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def schema_columns(inspector, table):
    return [{**column, "type": str(column["type"])} for column in inspector.get_columns(table)]


@pytest.fixture
def engine(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'users.db'}"
    command.upgrade(migration_config(database_url), "head")
    bind = create_engine(database_url, connect_args={"check_same_thread": False})

    @event.listens_for(bind, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    try:
        yield bind
    finally:
        bind.dispose()


def test_users_and_optional_ownership(engine):
    assert any(
        index["column_names"] == ["user_id"]
        for index in inspect(engine).get_indexes("conversations")
    )
    with Session(engine) as session:
        user = User(email="alex@example.com")
        owned = Conversation(user=user)
        anonymous = Conversation()
        session.add_all([owned, anonymous])
        session.commit()
        session.expire_all()

        assert user.id
        assert user.created_at is not None
        assert owned.user_id == user.id
        assert owned.user is user
        assert user.conversations == [owned]
        assert anonymous.user_id is None
        assert anonymous.user is None


@pytest.mark.parametrize("email", [None, "alex@example.com"])
def test_email_constraints(engine, email):
    with Session(engine) as session:
        session.add(User(email="alex@example.com"))
        session.commit()
        session.add(User(email=email))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_unknown_user_rejected_with_foreign_keys_enabled(engine):
    with Session(engine) as session:
        session.add(Conversation(user_id="missing"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_deleting_user_retains_conversation_and_messages(engine):
    with Session(engine) as session:
        user = User(email="alex@example.com")
        conversation = Conversation(user=user)
        message = Message(conversation=conversation, role="user", content="Hello")
        session.add(message)
        session.commit()
        conversation_id, message_id = conversation.id, message.id
        session.expire_all()
        session.delete(user)
        session.commit()
        assert session.get(Conversation, conversation_id).user_id is None
        assert session.get(Message, message_id).content == "Hello"


def test_upgrade_preserves_data_and_can_be_repeated(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'upgrade.db'}"
    config = migration_config(database_url)
    command.upgrade(config, "20260929_0001")
    engine = create_engine(database_url)
    try:
        initial = inspect(engine)
        conversation_columns = schema_columns(initial, "conversations")
        message_columns = schema_columns(initial, "messages")
        message_foreign_keys = initial.get_foreign_keys("messages")
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO conversations (id, title) VALUES ('old', 'Existing')"
            )
            connection.exec_driver_sql(
                "INSERT INTO messages (id, conversation_id, role, content) "
                "VALUES ('msg', 'old', 'user', 'Hello')"
            )
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        command.check(config)
        migrated = inspect(engine)
        assert [
            column
            for column in schema_columns(migrated, "conversations")
            if column["name"] != "user_id"
        ] == conversation_columns
        assert schema_columns(migrated, "messages") == message_columns
        assert migrated.get_foreign_keys("messages") == message_foreign_keys
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        with Session(engine) as session:
            conversation = session.get(Conversation, "old")
            assert conversation.title == "Existing"
            assert conversation.user_id is None
            assert session.get(Message, "msg").content == "Hello"
            conversation.user = User(email="alex@example.com")
            session.commit()
            assert session.scalar(select(User)).conversations == [conversation]
            session.add(User(email="alex@example.com"))
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()
        foreign_keys = inspect(engine).get_foreign_keys("conversations")
        assert any(
            fk["constrained_columns"] == ["user_id"] and fk["referred_table"] == "users"
            for fk in foreign_keys
        )
        assert any(
            index["column_names"] == ["user_id"]
            for index in inspect(engine).get_indexes("conversations")
        )

        command.downgrade(config, "20260929_0001")
        inspector = inspect(engine)
        assert "users" not in inspector.get_table_names()
        assert schema_columns(inspector, "conversations") == conversation_columns
        assert schema_columns(inspector, "messages") == message_columns
        assert inspector.get_foreign_keys("messages") == message_foreign_keys
        assert inspector.get_indexes("conversations") == []
        assert inspector.get_foreign_keys("conversations") == []
        with engine.connect() as connection:
            assert (
                connection.exec_driver_sql(
                    "SELECT title FROM conversations WHERE id = 'old'"
                ).scalar()
                == "Existing"
            )
            assert (
                connection.exec_driver_sql("SELECT content FROM messages WHERE id = 'msg'").scalar()
                == "Hello"
            )
        command.upgrade(config, "head")
        with Session(engine) as session:
            assert session.get(Conversation, "old").user_id is None
            assert session.get(Message, "msg").content == "Hello"
    finally:
        engine.dispose()


def test_chat_flow_after_migration(engine, monkeypatch):
    sessions = sessionmaker(bind=engine)

    def override_db():
        with sessions() as session:
            yield session

    provider = Mock()
    provider.generate_reply.return_value = "Hello back"
    monkeypatch.setattr(chat, "get_llm_provider", lambda: provider)
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            response = client.post("/api/conversations", json={"title": "Migrated chat"})
            assert response.status_code == 200
            conversation_id = response.json()["id"]
            response = client.post(
                f"/api/conversations/{conversation_id}/messages", json={"content": "Hello"}
            )
            assert response.status_code == 200
            assert response.json()["content"] == "Hello back"
            response = client.get(f"/api/conversations/{conversation_id}")
            assert response.status_code == 200
            assert [message["content"] for message in response.json()["messages"]] == [
                "Hello",
                "Hello back",
            ]
            response = client.get("/api/conversations")
            assert response.status_code == 200
            assert any(item["id"] == conversation_id for item in response.json())
        provider.generate_reply.assert_called_once_with([{"role": "user", "content": "Hello"}])
        with sessions() as session:
            conversation = session.get(Conversation, conversation_id)
            assert conversation.user_id is None
            conversation.user = User(email="owner@example.com")
            session.commit()
            assert len(conversation.messages) == 2
            assert conversation.user.conversations == [conversation]
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
