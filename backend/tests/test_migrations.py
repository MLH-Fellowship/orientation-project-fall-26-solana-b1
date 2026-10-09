from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect, text

from app.config import Settings


BACKEND_DIR = Path(__file__).parents[1]


def test_initial_migration_upgrades_and_downgrades(tmp_path):
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{database_path}"
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert {"conversations", "messages"}.issubset(inspector.get_table_names())
    assert {column["name"] for column in inspector.get_columns("messages")} == {
        "id",
        "conversation_id",
        "role",
        "content",
        "created_at",
    }
    password_column = next(
        column for column in inspector.get_columns("users") if column["name"] == "password_hash"
    )
    assert password_column["nullable"]
    foreign_key = inspector.get_foreign_keys("messages")[0]
    assert foreign_key["referred_table"] == "conversations"
    assert foreign_key["options"]["ondelete"] == "CASCADE"

    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys = ON"))
        connection.execute(text("INSERT INTO conversations (id) VALUES ('conversation-1')"))
        connection.execute(
            text(
                "INSERT INTO messages (id, conversation_id, role, content) "
                "VALUES ('message-1', 'conversation-1', 'user', 'hello')"
            )
        )
        connection.execute(text("DELETE FROM conversations WHERE id = 'conversation-1'"))
        assert connection.execute(text("SELECT COUNT(*) FROM messages")).scalar() == 0

    command.downgrade(config, "base")

    inspector = inspect(engine)
    assert "conversations" not in inspector.get_table_names()
    assert "messages" not in inspector.get_table_names()


def test_settings_reject_empty_database_url():
    with pytest.raises(ValidationError, match="DATABASE_URL must not be empty"):
        Settings(database_url="", jwt_secret="a" * 32)


def test_settings_reject_short_jwt_secret():
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(jwt_secret="short")
