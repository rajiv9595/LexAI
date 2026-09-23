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


class ValidatedAssistantReference(BaseModel):
    """Frontend-safe, backend-validated reference metadata (STEP 21).

    Serialized ONLY from STEP 20 citation-validated references, never from
    raw model output. Exposes validated source metadata and nothing else:
    no URLs, no provider internals, no prompts, no secrets.
    """

    source_id: str = Field(..., description="Stable id of the retrieved source")
    title: str = Field(..., description="Validated record title")
    citation_label: str = Field(..., description="Validated citation label")
    source_type: str = Field(..., description="Validated controlled source type")
    jurisdiction: Optional[str] = Field(
        default=None, description="Validated jurisdiction, if available"
    )
    prototype: bool = Field(
        default=True,
        description="Backend-validated prototype flag; never model-supplied",
    )


class AssistantMessageResponse(BaseModel):
    """Deterministic prototype assistant reply."""

    conversation_id: str
    message_id: str
    role: str = "assistant"
    content: str
    prototype: bool = True
    references: list[ValidatedAssistantReference] = Field(default_factory=list)


class AssistantConversationMessage(BaseModel):
    """Single stored prototype conversation message."""

    message_id: str
    role: str
    content: str
    references: list[ValidatedAssistantReference] = Field(default_factory=list)


class AssistantConversationResponse(BaseModel):
    """Prototype conversation payload."""

    conversation_id: str
    messages: list[AssistantConversationMessage]
    prototype: bool = True


class AssistantConversationListItem(BaseModel):
    """Lightweight STEP 24 discovery item for one user-owned conversation.

    Intentionally excludes messages, references, prompts, retrieved
    context, and provider data. Reference provenance is only available
    through the detail endpoint.
    """

    conversation_id: str
    updated_at: str = Field(
        ..., description="Last-activity timestamp (ISO 8601) for sorting"
    )
    message_count: int = Field(..., description="Total stored messages")
    first_user_message_preview: Optional[str] = Field(
        default=None,
        description="Truncated earliest user message, or null when none",
    )


class AssistantConversationListResponse(BaseModel):
    """Paginated STEP 24 conversation list."""

    items: list[AssistantConversationListItem] = Field(default_factory=list)
    page: int
    page_size: int
    total: int
