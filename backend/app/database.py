"""
Database engine and session management (SQLAlchemy).

Schema changes are managed by Alembic. Run `alembic upgrade head` from
the backend directory before starting the application.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


def create_database_engine(database_url):
    is_sqlite = make_url(database_url).get_backend_name() == "sqlite"
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    bind = create_engine(database_url, connect_args=connect_args)
    if is_sqlite:

        @event.listens_for(bind, "connect")
        def enable_foreign_keys(connection, _):
            cursor = connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()

    return bind


engine = create_database_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
