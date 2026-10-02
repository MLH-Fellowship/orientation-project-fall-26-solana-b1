import pytest
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Conversation, Message, User
from scripts.upgrade_user_model import upgrade


@pytest.fixture
def engine():
    bind = create_engine("sqlite://")

    @event.listens_for(bind, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    yield bind
    bind.dispose()


def test_users_and_optional_ownership(engine):
    Base.metadata.create_all(engine)
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
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(User(email="alex@example.com"))
        session.commit()
        session.add(User(email=email))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_unknown_user_rejected_with_foreign_keys_enabled(engine):
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Conversation(user_id="missing"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_deleting_user_retains_conversation_and_messages(engine):
    Base.metadata.create_all(engine)
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


def test_upgrade_preserves_data_and_can_be_repeated(engine):
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE conversations (id VARCHAR PRIMARY KEY, title VARCHAR, created_at DATETIME)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE messages (id VARCHAR PRIMARY KEY, conversation_id VARCHAR NOT NULL "
            "REFERENCES conversations(id), role VARCHAR NOT NULL, content TEXT NOT NULL, created_at DATETIME)"
        )
        connection.exec_driver_sql("INSERT INTO conversations (id, title) VALUES ('old', 'Existing')")
        connection.exec_driver_sql(
            "INSERT INTO messages (id, conversation_id, role, content) "
            "VALUES ('msg', 'old', 'user', 'Hello')"
        )
    upgrade(engine)
    upgrade(engine)
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
    assert any(fk["constrained_columns"] == ["user_id"] and fk["referred_table"] == "users" for fk in foreign_keys)
    assert any(
        index["column_names"] == ["user_id"]
        for index in inspect(engine).get_indexes("conversations")
    )
