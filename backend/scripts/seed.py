"""Populate the development database with sample chat history."""

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Conversation, Message


SEED_CONVERSATIONS = (
    {
        "id": "00000000-0000-4000-8000-000000000001",
        "title": "Solana developer onboarding",
        "messages": (
            {
                "id": "00000000-0000-4000-8000-000000000101",
                "role": "user",
                "content": "What should I learn before building my first Solana program?",
            },
            {
                "id": "00000000-0000-4000-8000-000000000102",
                "role": "assistant",
                "content": "Start with accounts, transactions, and program-derived addresses.",
            },
        ),
    },
    {
        "id": "00000000-0000-4000-8000-000000000002",
        "title": "Local testing workflow",
        "messages": (
            {
                "id": "00000000-0000-4000-8000-000000000201",
                "role": "user",
                "content": "How can I test the chat interface without an API key?",
            },
            {
                "id": "00000000-0000-4000-8000-000000000202",
                "role": "assistant",
                "content": "Load seeded conversations and exercise the UI against local data.",
            },
        ),
    },
)


def seed_database(db: Session) -> int:
    """Insert missing sample conversations and return the number created."""
    created = 0

    for seed in SEED_CONVERSATIONS:
        if db.get(Conversation, seed["id"]) is not None:
            continue

        conversation = Conversation(id=seed["id"], title=seed["title"])
        conversation.messages = [
            Message(id=message["id"], role=message["role"], content=message["content"])
            for message in seed["messages"]
        ]
        db.add(conversation)
        created += 1

    db.commit()
    return created


def main() -> None:
    with SessionLocal() as db:
        created = seed_database(db)
    print(f"Created {created} sample conversations.")


if __name__ == "__main__":
    main()
