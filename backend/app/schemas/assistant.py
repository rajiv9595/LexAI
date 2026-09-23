"""Assistant request/response schemas."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AssistantMessageRequest(BaseModel):
    """Incoming user message for the prototype assistant."""

    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = Field(default=None, max_length=128)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be empty or whitespace only")
        return value


class AssistantMessageResponse(BaseModel):
    """Deterministic prototype assistant reply."""

    conversation_id: str
    message_id: str
    role: str = "assistant"
    content: str
    prototype: bool = True


class AssistantConversationMessage(BaseModel):
    """Single stored prototype conversation message."""

    message_id: str
    role: str
    content: str


class AssistantConversationResponse(BaseModel):
    """Prototype conversation payload."""

    conversation_id: str
    messages: list[AssistantConversationMessage]
    prototype: bool = True
