"""Add issue #6's schema to an existing SQLite database without deleting data."""

from sqlalchemy import inspect

from app.database import engine
from app.models import User


def upgrade(bind):
    if bind.dialect.name != "sqlite":
        raise ValueError("This upgrade supports SQLite only")

    with bind.begin() as connection:
        inspector = inspect(connection)
        if not inspector.has_table("conversations"):
            raise ValueError("Expected an existing conversations table")
        columns = {column["name"] for column in inspector.get_columns("conversations")}
        User.__table__.create(connection, checkfirst=True)
        if "user_id" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE conversations ADD COLUMN user_id VARCHAR REFERENCES users(id)"
            )


if __name__ == "__main__":
    upgrade(engine)
    print("User model upgrade complete.")
