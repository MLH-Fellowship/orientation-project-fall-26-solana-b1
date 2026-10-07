from pathlib import Path
import shutil

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.database import create_database_engine


BACKEND_DIR = Path(__file__).parents[1]


def migration_config(url):
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def test_application_enforces_foreign_keys_on_new_connections(tmp_path):
    url = f"sqlite:///{tmp_path / 'application.db'}"
    command.upgrade(migration_config(url), "head")
    engine = create_database_engine(url)
    try:
        # Concurrent checkouts and disposal both require fresh physical connections.
        with engine.connect() as first, engine.connect() as second:
            assert first.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
            assert second.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        engine.dispose()
        with engine.begin() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
            for statement in (
                "INSERT INTO conversations (id, user_id) VALUES ('chat', 'missing')",
                "INSERT INTO messages (id, conversation_id, role, content) "
                "VALUES ('msg', 'missing', 'user', 'Hello')",
            ):
                with pytest.raises(IntegrityError):
                    connection.exec_driver_sql(statement)
            connection.exec_driver_sql(
                "INSERT INTO users (id, email) VALUES ('user', 'a@example.com')"
            )
            connection.exec_driver_sql(
                "INSERT INTO conversations (id, user_id) VALUES ('chat', 'user')"
            )
            connection.exec_driver_sql(
                "INSERT INTO messages (id, conversation_id, role, content) "
                "VALUES ('msg', 'chat', 'user', 'Hello')"
            )
            with pytest.raises(IntegrityError):
                connection.exec_driver_sql("DELETE FROM users WHERE id='user'")
            connection.exec_driver_sql("DELETE FROM conversations WHERE id='chat'")
            assert connection.exec_driver_sql("SELECT COUNT(*) FROM messages").scalar() == 0
    finally:
        engine.dispose()


def test_batch_migrations_preserve_messages_with_enforcement_default_on(tmp_path):
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    config = migration_config(url)
    command.upgrade(config, "20260929_0001")
    engine = create_database_engine(url)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO conversations (id, title) VALUES ('chat', 'Keep me')"
        )
        connection.exec_driver_sql(
            "INSERT INTO messages (id, conversation_id, role, content) "
            "VALUES ('msg', 'chat', 'user', 'Keep this message')"
        )

    def enable_by_default(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    event.listen(Engine, "connect", enable_by_default)
    try:
        for revision, action in (
            ("head", command.upgrade),
            ("20260929_0001", command.downgrade),
            ("head", command.upgrade),
        ):
            action(config, revision)
            with engine.connect() as connection:
                assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
                assert (
                    connection.exec_driver_sql(
                        "SELECT title FROM conversations WHERE id='chat'"
                    ).scalar()
                    == "Keep me"
                )
                assert (
                    connection.exec_driver_sql(
                        "SELECT content FROM messages WHERE id='msg'"
                    ).scalar()
                    == "Keep this message"
                )
                assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        command.check(config)
    finally:
        event.remove(Engine, "connect", enable_by_default)
        engine.dispose()


@pytest.mark.parametrize("invalid_table", ["conversations", "messages"])
@pytest.mark.parametrize(
    "revision, action", [("head", command.upgrade), ("20260929_0001", command.downgrade)]
)
def test_existing_invalid_references_block_migrations_without_cleanup(
    tmp_path, invalid_table, revision, action
):
    url = f"sqlite:///{tmp_path / 'invalid.db'}"
    config = migration_config(url)
    command.upgrade(config, "head")
    engine = create_engine(url)
    try:
        statement = (
            "INSERT INTO conversations (id, user_id) VALUES ('invalid', 'missing')"
            if invalid_table == "conversations"
            else "INSERT INTO messages (id, conversation_id, role, content) VALUES ('invalid', 'missing', 'user', 'Keep me')"
        )
        with engine.begin() as connection:
            connection.exec_driver_sql(statement)
        with pytest.raises(RuntimeError, match=f"foreign-key violations in: {invalid_table}"):
            action(config, revision)
        with engine.connect() as connection:
            assert connection.exec_driver_sql(f"SELECT COUNT(*) FROM {invalid_table}").scalar() == 1
            assert (
                connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()
                == "20261005_0003"
            )
        assert "users" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_post_migration_integrity_failure_rolls_back_schema_and_data(tmp_path):
    url = f"sqlite:///{tmp_path / 'rollback.db'}"
    config = migration_config(url)
    command.upgrade(config, "head")
    migrations = tmp_path / "migrations"
    shutil.copytree(BACKEND_DIR / "migrations", migrations)
    (migrations / "versions" / "test_invalid.py").write_text("""
from alembic import op
import sqlalchemy as sa
revision = "test_invalid"
down_revision = "20261005_0003"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("test_marker", sa.Column("id", sa.Integer(), primary_key=True))
    op.execute("INSERT INTO conversations (id, user_id) VALUES ('invalid', 'missing')")

def downgrade():
    op.drop_table("test_marker")
""")
    config.set_main_option("script_location", str(migrations))
    with pytest.raises(RuntimeError, match="foreign-key violations"):
        command.upgrade(config, "head")
    engine = create_database_engine(url)
    try:
        assert "test_marker" not in inspect(engine).get_table_names()
        with engine.connect() as connection:
            assert connection.exec_driver_sql("SELECT COUNT(*) FROM conversations").scalar() == 0
            assert (
                connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()
                == "20261005_0003"
            )
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
    finally:
        engine.dispose()
