"""Pydantic request/response schemas."""
from datetime import datetime

from typing import Annotated

from pydantic import BaseModel, StringConstraints


class MessageCreate(BaseModel):
    content: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)
    ]


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationUpdate(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = []
