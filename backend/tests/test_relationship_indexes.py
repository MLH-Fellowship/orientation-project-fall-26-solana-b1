from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Conversation, Message, User


def migration_config(url):
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    return config


@pytest.fixture
def engine(tmp_path):
    url = f"sqlite:///{tmp_path / 'relationships.db'}"
    command.upgrade(migration_config(url), "head")
    bind = create_engine(url)

    @event.listens_for(bind, "connect")
    def enforce_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    try:
        yield bind
    finally:
        bind.dispose()


def test_message_index_upgrade_and_rollback_preserve_data_and_foreign_keys(tmp_path):
    url = f"sqlite:///{tmp_path / 'indexes.db'}"
    config = migration_config(url)
    command.upgrade(config, "20261003_0002")
    bind = create_engine(url)
    try:
        original = inspect(bind)
        assert original.get_indexes("messages") == []
        ownership_indexes = original.get_indexes("conversations")
        foreign_keys = original.get_foreign_keys("messages")
        with Session(bind) as session:
            user = User(email="owner@example.com")
            chat = Conversation(user=user, title="Keep me")
            session.add(Message(conversation=chat, role="user", content="Keep this message"))
            session.commit()
            chat_id = chat.id

        for action, revision in (
            (command.upgrade, "head"),
            (command.upgrade, "head"),
            (command.downgrade, "20261003_0002"),
            (command.upgrade, "head"),
        ):
            action(config, revision)
            inspector = inspect(bind)
            assert inspector.get_indexes("conversations") == ownership_indexes
            assert inspector.get_foreign_keys("messages") == foreign_keys
            indexes = inspector.get_indexes("messages")
            if revision == "head":
                assert len(indexes) == 1
                assert indexes[0]["name"] == "ix_messages_conversation_id"
                assert indexes[0]["column_names"] == ["conversation_id"]
                assert not indexes[0]["unique"]
            else:
                assert indexes == []
            with Session(bind) as session:
                chat = session.get(Conversation, chat_id)
                assert chat.title == "Keep me"
                assert chat.user.email == "owner@example.com"
                assert [message.content for message in chat.messages] == ["Keep this message"]
            with bind.connect() as connection:
                assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        assert ownership_indexes[0]["column_names"] == ["user_id"]
        command.check(config)
    finally:
        bind.dispose()


@pytest.mark.parametrize("load_relationships", [False, True])
def test_orm_conversation_deletion_preserves_user_and_other_chats(engine, load_relationships):
    with Session(engine) as session:
        user = User(email="owner@example.com")
        deleted = Conversation(user=user)
        retained = Conversation(user=user)
        session.add_all(
            [
                Message(conversation=deleted, role="user", content="Delete me"),
                Message(conversation=retained, role="user", content="Keep me"),
            ]
        )
        session.commit()
        deleted_id, retained_id, user_id = deleted.id, retained.id, user.id
        session.expire_all()
        if load_relationships:
            assert len(deleted.messages) == 1
        session.delete(deleted)
        session.commit()
        assert session.get(Conversation, deleted_id) is None
        assert session.get(User, user_id) is not None
        assert session.get(Conversation, retained_id).messages[0].content == "Keep me"
        assert session.query(Message).count() == 1


def test_removing_message_from_relationship_deletes_only_that_message(engine):
    with Session(engine) as session:
        chat = Conversation()
        removed = Message(conversation=chat, role="user", content="Remove me")
        retained = Message(conversation=chat, role="assistant", content="Keep me")
        session.add(chat)
        session.commit()
        removed_id, retained_id, chat_id = removed.id, retained.id, chat.id
        chat.messages.remove(removed)
        session.commit()
        assert session.get(Message, removed_id) is None
        assert session.get(Message, retained_id).content == "Keep me"
        assert session.get(Conversation, chat_id) is not None


def test_direct_sql_deletion_rules_with_enforcement_enabled(engine):
    with Session(engine) as session:
        user = User(email="owner@example.com")
        first = Conversation(user=user)
        second = Conversation(user=user)
        session.add_all(
            [
                Message(conversation=first, role="user", content="Delete me"),
                Message(conversation=second, role="user", content="Keep me"),
            ]
        )
        session.commit()
        first_id, second_id, user_id = first.id, second.id, user.id
    with engine.begin() as connection:
        with pytest.raises(IntegrityError):
            connection.exec_driver_sql("DELETE FROM users WHERE id=?", (user_id,))
        connection.exec_driver_sql("DELETE FROM conversations WHERE id=?", (first_id,))
        assert connection.exec_driver_sql("SELECT COUNT(*) FROM messages").scalar() == 1
        connection.exec_driver_sql("UPDATE conversations SET user_id=NULL WHERE id=?", (second_id,))
        connection.exec_driver_sql("DELETE FROM users WHERE id=?", (user_id,))
    with Session(engine) as session:
        assert session.get(User, user_id) is None
        chat = session.get(Conversation, second_id)
        assert chat.user_id is None
        assert chat.messages[0].content == "Keep me"
