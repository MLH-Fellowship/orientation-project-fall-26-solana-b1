"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class AuthCredentials(BaseModel):
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class SignupOut(BaseModel):
    message: Literal["Signup successful"] = "Signup successful"


class UserOut(BaseModel):
    id: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
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


class ConversationUsageOut(BaseModel):
    conversation_id: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


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
