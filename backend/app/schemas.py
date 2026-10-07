"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class MessageCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"content": "Explain how this project stores conversations."}]
        }
    )

    content: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)
    ]


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


class ConversationListOut(BaseModel):
    items: list[ConversationOut]
    total: int
    limit: int
    offset: int


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = []


class HealthOut(BaseModel):
    status: Literal["ok"] = Field(description="Application is responding.")


class ErrorOut(BaseModel):
    detail: str = Field(examples=["Conversation not found"])


class ValidationErrorDetail(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class ValidationErrorOut(BaseModel):
    detail: list[ValidationErrorDetail] = Field(
        examples=[
            [
                {
                    "loc": ["body", "content"],
                    "msg": "String should have at least 1 character",
                    "type": "string_too_short",
                }
            ]
        ]
    )
