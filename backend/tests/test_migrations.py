from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


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
    assert (
        inspector.get_foreign_keys("messages")[0]["referred_table"] == "conversations"
    )

    command.downgrade(config, "base")

    inspector = inspect(engine)
    assert "conversations" not in inspector.get_table_names()
    assert "messages" not in inspector.get_table_names()
