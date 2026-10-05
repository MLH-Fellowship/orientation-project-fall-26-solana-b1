"""
Core conversation + messaging endpoints.

This is the minimum needed for the UI to create a conversation, send a
message, and get an LLM reply back. Pagination, streaming, rename,
delete, etc. are left as fellow issues -- see ISSUES.md.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.llm import get_llm_provider
from app.models import Conversation, Message
from app.schemas import (
    ConversationCreate,
    ConversationDetailOut,
    ConversationOut,
    ConversationUpdate,
    ErrorOut,
    MessageCreate,
    MessageOut,
    ValidationErrorOut,
)

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


@router.patch(
    "/{conversation_id}",
    response_model=ConversationOut,
    summary="Rename a conversation",
    description="Update a conversation's title. The title is trimmed and must be 1-200 characters.",
    responses={
        404: {"model": ErrorOut, "description": "Conversation not found"},
        422: {"model": ValidationErrorOut, "description": "Invalid conversation ID or title"},
    },
)
def rename_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
):
    convo = db.get(Conversation, str(conversation_id))
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    convo.title = payload.title
    db.commit()
    db.refresh(convo)
    return convo


@router.delete(
    "/{conversation_id}",
    status_code=204,
    summary="Delete a conversation",
    description="Delete a conversation and all of its messages.",
    responses={
        404: {"model": ErrorOut, "description": "Conversation not found"},
        422: {"model": ValidationErrorOut, "description": "Invalid conversation ID"},
    },
)
def delete_conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    convo = db.get(Conversation, str(conversation_id))
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(convo)  # cascades to messages via the ORM relationship
    db.commit()


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

    user_msg = Message(conversation_id=conversation_id, role="user", content=payload.content)
    db.add(user_msg)
    # Flush, not commit: if the LLM call fails the session rolls back,
    # so a retry from the UI doesn't save the user message twice.
    db.flush()

    history = [{"role": m.role, "content": m.content} for m in convo.messages]

    llm = get_llm_provider()
    reply_text = llm.generate_reply(history)

    assistant_msg = Message(conversation_id=conversation_id, role="assistant", content=reply_text)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    return assistant_msg
