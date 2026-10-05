"""
Core conversation + messaging endpoints.

This is the minimum needed for the UI to create a conversation, send a
message, and get an LLM reply back. Pagination, streaming, rename,
delete, etc. are left as fellow issues -- see ISSUES.md.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.llm import get_llm_provider
from app.models import Conversation, Message
from app.schemas import (
    ConversationCreate,
    ConversationDetailOut,
    ConversationOut,
    ErrorOut,
    MessageCreate,
    MessageOut,
    ValidationErrorOut,
)
from app.utils.titles import DEFAULT_TITLE, resolve_title

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post(
    "",
    response_model=ConversationOut,
    summary="Create a conversation",
    description="Create an empty conversation with an optional title. No LLM call is made.",
)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    convo = Conversation(title=payload.title or "New Conversation")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


@router.get(
    "",
    response_model=list[ConversationOut],
    summary="List conversations",
    description="Return all conversations, newest first, without message bodies.",
)
def list_conversations(db: Session = Depends(get_db)):
    return db.query(Conversation).order_by(Conversation.created_at.desc()).all()


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailOut,
    summary="Get a conversation with its messages",
    description="Look up a conversation by ID and return its saved messages.",
    responses={404: {"model": ErrorOut, "description": "Conversation not found"}},
)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    convo = db.get(Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageOut,
    summary="Send a message and receive an assistant reply",
    description=(
        "Save the user message, call the configured LLM with conversation history, "
        "then save and "
        "return the assistant reply. Requires a configured LLM API key. "
    ),
    responses={
        404: {"model": ErrorOut, "description": "Conversation not found"},
        422: {"model": ValidationErrorOut, "description": "Invalid message content"},
    },
)
def send_message(conversation_id: str, payload: MessageCreate, db: Session = Depends(get_db)):
    convo = db.get(Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    is_first_exchange = len(convo.messages) == 0

    user_msg = Message(conversation_id=conversation_id, role="user", content=payload.content)
    db.add(user_msg)
    # Flush, not commit: if the LLM call fails the session rolls back,
    # so a retry from the UI doesn't save the user message twice.
    db.flush()
    db.refresh(convo)

    history = [{"role": m.role, "content": m.content} for m in convo.messages]

    llm = get_llm_provider()
    reply_text = llm.generate_reply(history)

    assistant_msg = Message(conversation_id=conversation_id, role="assistant", content=reply_text)
    db.add(assistant_msg)
    db.commit()

    if is_first_exchange and convo.title == DEFAULT_TITLE:
        convo.title = resolve_title(
            payload.content,
            reply_text,
            lambda: llm.generate_title(payload.content, reply_text),
        )
        db.commit()

    db.refresh(assistant_msg)
    return assistant_msg
