"""
Core conversation + messaging endpoints.

This is the minimum needed for the UI to create a conversation, send a
message, and get an LLM reply back. Pagination, streaming, rename,
delete, etc. are left as fellow issues -- see ISSUES.md.
"""

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.llm import get_llm_provider
from app.models import Conversation, Message
from app.schemas import (
    ConversationCreate,
    ConversationDetailOut,
    ConversationOut,
    ErrorResponse,
    MessageCreate,
    MessageOut,
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
    responses={404: {"model": ErrorResponse, "description": "Conversation not found"}},
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
        404: {"model": ErrorResponse, "description": "Conversation not found"},
        422: {"model": ErrorResponse, "description": "Invalid message content"},
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


@router.post(
    "/{conversation_id}/messages/stream",
    summary="Stream an assistant reply",
    description="Save a user message and stream the assistant reply as newline-delimited JSON.",
    responses={
        404: {"model": ErrorResponse, "description": "Conversation not found"},
        422: {"model": ErrorResponse, "description": "Invalid message content"},
    },
)
def stream_message(
    conversation_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
):
    if not db.get(Conversation, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    stream_session_factory = sessionmaker(autoflush=False, bind=db.get_bind())

    def events() -> Iterator[str]:
        stream_db = stream_session_factory()
        reply_parts: list[str] = []
        try:
            convo = stream_db.get(Conversation, conversation_id)
            user_msg = Message(
                conversation_id=conversation_id, role="user", content=payload.content
            )
            stream_db.add(user_msg)
            stream_db.flush()
            history = [{"role": m.role, "content": m.content} for m in convo.messages]

            for chunk in get_llm_provider().generate_reply_stream(history):
                reply_parts.append(chunk)
                yield json.dumps({"type": "chunk", "text": chunk}) + "\n"

            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content="".join(reply_parts),
            )
            stream_db.add(assistant_msg)
            stream_db.commit()
            yield (
                json.dumps(
                    {
                        "type": "done",
                        "message": MessageOut.model_validate(assistant_msg).model_dump(mode="json"),
                    }
                )
                + "\n"
            )
        except Exception as exc:
            stream_db.rollback()
            yield json.dumps({"type": "error", "message": str(exc)}) + "\n"
        finally:
            stream_db.close()

    return StreamingResponse(events(), media_type="application/x-ndjson")
