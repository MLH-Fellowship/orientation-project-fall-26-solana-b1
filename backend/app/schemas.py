"""Pydantic request/response schemas."""
from fastapi.responses import JSONResponse
from datetime import datetime

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    
class ErrorResponse(BaseModel):
    error: ErrorDetail

class MessageCreate(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = []
