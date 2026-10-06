from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Conversation, Message
from scripts.seed import seed_database


def test_seed_database_is_idempotent(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'seed.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as db:
        assert seed_database(db) == 2
        assert seed_database(db) == 0

        conversations = db.query(Conversation).all()
        messages = db.query(Message).all()

        assert len(conversations) == 2
        assert len(messages) == 4
        assert {message.role for message in messages} == {"user", "assistant"}
