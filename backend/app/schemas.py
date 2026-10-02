"""Pydantic request/response schemas."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"content": "Explain how this project stores conversations."}]
    })

    content: str


class MessageOut(BaseModel):
    id: str
    role: str = Field(examples=["assistant"])
    content: str = Field(examples=["Conversations are stored in SQLite."])
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: str | None = Field(
        default=None,
        description="Optional title; defaults to New Conversation.",
        examples=["Learning FastAPI"],
    )


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = []


class HealthOut(BaseModel):
    status: Literal["ok"] = Field(description="Application is responding.")


class ErrorOut(BaseModel):
    detail: str = Field(examples=["Conversation not found"])
