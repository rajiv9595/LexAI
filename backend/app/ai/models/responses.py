"""Strongly typed AI request, response, and domain-level legal models."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SafetyStatus(str, Enum):
    """Deterministic safety risk classifications for legal queries."""

    SAFE = "safe"
    CAUTION = "caution"
    ESCALATE = "escalate"


class SafetyFlag(BaseModel):
    """Categorized safety trigger detected during request or response evaluation."""

    flag_name: str
    category: str
    description: str


class SafetyAssessment(BaseModel):
    """Structured pre- or post-generation safety assessment."""

    status: SafetyStatus = SafetyStatus.SAFE
    flags: list[SafetyFlag] = Field(default_factory=list)
    requires_professional_review: bool = False
    advisory_message: str = ""


class AIRequestMessage(BaseModel):
    """Single message in an AI conversation context."""

    role: str = Field(..., description="Role of the author, e.g., 'user', 'assistant', 'system'")
    content: str = Field(..., min_length=1, description="Text content of the message")


class AIRequest(BaseModel):
    """Provider-independent AI generation request."""

    system_instruction: str = Field(default="", description="Top-level system prompt instruction")
    user_message: str = Field(..., min_length=1, description="Active user prompt or question")
    conversation_history: list[AIRequestMessage] = Field(
        default_factory=list, description="Prior conversation messages in chronological order"
    )
    retrieved_context: list[str] = Field(
        default_factory=list, description="Grounding knowledge chunks (for future RAG)"
    )
    case_context: dict[str, str] = Field(
        default_factory=dict, description="Structured user/case metadata"
    )
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=8192)
    response_schema_name: str = Field(
        default="legal_assistant",
        description="Structured output task: 'legal_assistant' or 'query_understanding'",
    )
    query_understanding: str = Field(
        default="",
        description="AI-derived query interpretation supplied as context to final-answer generation",
    )


class AIResponse(BaseModel):
    """Provider-independent raw AI generation response."""

    content: str = Field(..., description="Generated text content from the provider")
    provider: str = Field(..., description="Identifier of the AI provider (e.g., 'deterministic-mock', 'openai', 'gemini')")
    model: str = Field(..., description="Specific model name or version used")
    finish_reason: str = Field(default="stop", description="Generation completion reason")
    safety_status: SafetyStatus = Field(default=SafetyStatus.SAFE)
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class LegalReferenceItem(BaseModel):
    """Structured reference to a legal source, statute, or concept.

    STEP 20 grounding: a reference is only valid when it is bound to an
    actually retrieved source. ``source_id`` carries the stable id of the
    retrieved record; the backend citation validator rebuilds ``title``,
    ``kind``, ``citation``, ``jurisdiction``, and ``prototype`` from the
    ``GroundedContext`` source of truth rather than trusting model output.
    """

    title: str
    kind: str
    citation: str = ""
    relevance_note: str = ""
    source_id: str = Field(
        default="",
        description="Stable id of the retrieved source; empty when unbound",
    )
    jurisdiction: str | None = Field(
        default=None,
        description="Source jurisdiction copied from GroundedContext, if any",
    )
    prototype: bool = Field(
        default=True,
        description=(
            "True unless the backend validator confirms a non-prototype "
            "retrieved source; fail-safe toward prototype/unverified"
        ),
    )


class LegalAssistantResponse(BaseModel):
    """Domain-level structured response contract for legal assistance."""

    answer: str = Field(..., description="Primary legal information response text")
    issue_summary: str = Field(default="", description="Concise summary of identified legal issues")
    assumptions: list[str] = Field(default_factory=list, description="Assumptions made in the response")
    missing_information: list[str] = Field(default_factory=list, description="Key facts needed for full analysis")
    potential_considerations: list[str] = Field(default_factory=list, description="Legal principles and considerations")
    suggested_next_steps: list[str] = Field(default_factory=list, description="Actionable recommendations")
    references: list[LegalReferenceItem] = Field(default_factory=list, description="Cited legal authorities or references")
    disclaimer: str = Field(..., description="Mandatory legal disclaimer text")
    safety_assessment: SafetyAssessment = Field(default_factory=SafetyAssessment)
    prompt_version: str = Field(default="", description="Version tag of the prompt used")
    provider_used: str = Field(default="", description="Provider responsible for generation")
