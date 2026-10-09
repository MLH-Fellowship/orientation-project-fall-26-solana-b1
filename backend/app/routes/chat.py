"""
Core conversation + messaging endpoints.

This is the minimum needed for the UI to create a conversation, send a
message, and get an LLM reply back. Pagination, streaming, rename,
delete, etc. are left as fellow issues -- see ISSUES.md.
"""

from uuid import UUID

from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.llm import get_llm_provider
from app.models import Conversation, Message
from app.rate_limit import limiter
from app.schemas import (
    ConversationCreate,
    ConversationDetailOut,
    ConversationListOut,
    ConversationOut,
    ConversationUpdate,
    ConversationUsageOut,
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
    response_model=ConversationListOut,
    summary="List conversations",
    description=(
        "Return conversations newest first, without message bodies. "
        "Supports limit/offset pagination. "
        "Defaults: limit=20, offset=0. "
        "limit is capped at 100."
    ),
)
def list_conversations(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ConversationListOut:
    total = db.query(Conversation).count()
    items = (
        db.query(Conversation)
        .order_by(Conversation.created_at.desc(), Conversation.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return ConversationListOut(items=items, total=total, limit=limit, offset=offset)


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


@router.get(
    "/{conversation_id}/usage",
    response_model=ConversationUsageOut,
    summary="Get conversation token usage",
    description=(
        "Return the saved prompt and completion token totals. "
        "Unknown counts are treated as zero. Title requests are excluded."
    ),
    responses={404: {"model": ErrorResponse, "description": "Conversation not found"}},
)
def get_usage(conversation_id: str, db: Session = Depends(get_db)):
    if db.get(Conversation, conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    prompt_tokens, completion_tokens = (
        db.query(
            func.coalesce(func.sum(Message.prompt_tokens), 0),
            func.coalesce(func.sum(Message.completion_tokens), 0),
        )
        .filter(Message.conversation_id == conversation_id)
        .one()
    )
    return ConversationUsageOut(
        conversation_id=conversation_id,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationOut,
    summary="Rename a conversation",
    description="Update a conversation's title. The title is trimmed and must be 1-200 characters.",
    responses={
        404: {"model": ErrorResponse, "description": "Conversation not found"},
        422: {"model": ErrorResponse, "description": "Invalid conversation ID or title"},
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
        404: {"model": ErrorResponse, "description": "Conversation not found"},
        422: {"model": ErrorResponse, "description": "Invalid conversation ID"},
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
        404: {"model": ErrorResponse, "description": "Conversation not found"},
        429: {"description": "Message rate limit exceeded"},
        422: {"model": ErrorResponse, "description": "Invalid message content"},
    },
)
@limiter.limit(lambda: settings.message_rate_limit)
def send_message(
    conversation_id: str,
    payload: MessageCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
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
    reply = llm.generate_reply(history)

    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=reply.text,
        prompt_tokens=reply.prompt_tokens,
        completion_tokens=reply.completion_tokens,
    )
    db.add(assistant_msg)
    db.commit()

    if is_first_exchange and convo.title == DEFAULT_TITLE:
        convo.title = resolve_title(
            payload.content,
            reply.text,
            lambda: llm.generate_title(payload.content, reply.text),
        )
        db.commit()

    db.refresh(assistant_msg)
    return assistant_msg
