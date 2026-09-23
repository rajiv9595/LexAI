"""Structured legal query understanding model.

Represents an AI-derived structural interpretation of a user's legal
question. This is analysis/extraction only: it never answers the legal
question, never provides legal conclusions, and never invents facts.
Unknown information stays unknown (None or empty).
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


LegalDomain = Literal[
    "landlord_tenant",
    "employment",
    "contract",
    "consumer",
    "family",
    "criminal",
    "civil_dispute",
    "property",
    "immigration",
    "intellectual_property",
    "corporate",
    "tax",
    "insurance",
    "personal_injury",
    "estate",
    "wills",
    "privacy",
    "technology",
    "regulatory",
    "other",
    "unknown",
]

LegalIntent = Literal[
    "general_information",
    "dispute_resolution",
    "legal_rights",
    "legal_obligations",
    "contract_review",
    "document_help",
    "procedure_guidance",
    "deadline_question",
    "risk_assessment",
    "compliance_question",
    "case_strategy_information",
    "explanation",
    "other",
]

QueryUrgency = Literal["normal", "time_sensitive", "urgent", "unknown"]

MAX_CLARIFICATION_QUESTIONS = 5


class LegalParty(BaseModel):
    """A party or entity involved in the legal issue."""

    role: str = Field(..., description="Role such as tenant, landlord, employee, employer")
    name: str | None = Field(
        default=None,
        description="Explicitly stated name, or null when not provided",
    )


class LegalQueryUnderstanding(BaseModel):
    """AI-derived structural interpretation of a user's legal question.

    Confidence reflects extraction/classification confidence only, never a
    legal-outcome probability. Urgency is informational; the existing
    safety guardrails remain authoritative.
    """

    intent: LegalIntent = Field(
        ..., description="AI interpretation of what the user is asking for"
    )
    legal_domain: LegalDomain = Field(
        ..., description="Best-fit legal domain, or 'unknown' when uncertain"
    )
    primary_issue: str | None = Field(
        default=None,
        description="Main legal issue in concise language, or null when unclear",
    )
    secondary_issues: list[str] = Field(
        default_factory=list,
        description="Additional explicitly supported issues",
    )
    jurisdiction: str | None = Field(
        default=None,
        description="Explicitly stated jurisdiction only; null when not provided",
    )
    parties: list[LegalParty] = Field(
        default_factory=list, description="Involved parties; names only when stated"
    )
    facts: list[str] = Field(
        default_factory=list,
        description="Facts explicitly stated by the user; allegations framed as user statements",
    )
    dates: list[str] = Field(
        default_factory=list,
        description="Date/time references as worded by the user",
    )
    amounts: list[str] = Field(
        default_factory=list,
        description="Monetary/quantitative amounts as worded by the user",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Relevant missing facts that could affect a later answer",
    )
    clarification_questions: list[str] = Field(
        default_factory=list,
        description="High-value clarification questions (at most 5)",
    )
    urgency: QueryUrgency = Field(
        default="unknown",
        description="Informational urgency only; safety guardrails remain authoritative",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Extraction/classification confidence, not outcome probability",
    )
    prompt_version: str = Field(
        default="", description="Version tag of the understanding prompt used"
    )

    @field_validator("clarification_questions")
    @classmethod
    def _limit_clarification_questions(cls, value: list[str]) -> list[str]:
        if len(value) > MAX_CLARIFICATION_QUESTIONS:
            raise ValueError(
                f"At most {MAX_CLARIFICATION_QUESTIONS} clarification questions allowed"
            )
        return value
