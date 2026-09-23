"""Provider-neutral AI interface and mock implementations."""

import json
import re
from abc import ABC, abstractmethod

from app.ai.models.responses import AIRequest, AIResponse, SafetyStatus


class AIProvider(ABC):
    """Abstract interface for LLM / AI generation providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique identifier for this provider."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Execute generation for the given AI request and return a structured response."""
        raise NotImplementedError


class MockDeterministicAIProvider(AIProvider):
    """Deterministic offline mock provider for testing and architectural verification."""

    def __init__(self, fixed_reply: str | None = None, model_name: str = "mock-v1"):
        self._fixed_reply = fixed_reply
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "deterministic-mock"

    def generate(self, request: AIRequest) -> AIResponse:
        if request.response_schema_name == "query_understanding":
            reply_text = json.dumps(_mock_query_understanding(request.user_message))
        else:
            reply_text = (
                self._fixed_reply
                if self._fixed_reply is not None
                else f"Deterministic response to: '{request.user_message[:60]}'"
            )
        return AIResponse(
            content=reply_text,
            provider=self.provider_name,
            model=self._model_name,
            finish_reason="stop",
            safety_status=SafetyStatus.SAFE,
            prompt_tokens=len(request.user_message.split()) + len(request.system_instruction.split()),
            completion_tokens=len(reply_text.split()),
        )


_DISPUTE_KEYWORDS = (
    "kept",
    "refusing",
    "refuse",
    "dispute",
    "hasn't",
    "haven't",
    "unpaid",
    "not paid",
    "terminated",
    "fired",
    "breach",
    "violated",
    "illegally",
    "what can i do",
    "complaint",
)

_AMOUNT_PATTERN = re.compile(r"₹[\d,]+|\$[\d,]+|€[\d,]+")

_DATE_PATTERN = re.compile(
    r"\b(yesterday|today|tomorrow|last week|last month|last year|"
    r"\d+\s+(?:days?|weeks?|months?|years?)\s+ago|"
    r"(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)(?:\s+\d{1,2})?)\b"
)


def _mock_query_understanding(user_message: str) -> dict:
    """Deterministic offline query understanding for tests and mock mode."""
    message = user_message.strip()
    text = message.lower()

    if any(k in text for k in ("landlord", "tenant", "rent", "rental", "deposit", "lease", "evict")):
        domain = "landlord_tenant"
    elif any(k in text for k in ("employer", "employee", "wage", "salary", "workplace", "paid me")):
        domain = "employment"
    elif any(k in text for k in ("contract", "agreement", "clause", "signed")):
        domain = "contract"
    else:
        domain = "unknown"

    if "deposit" in text:
        primary_issue: str | None = "security deposit dispute"
    elif any(k in text for k in ("hasn't paid", "haven't paid", "unpaid", "not paid")):
        primary_issue = "unpaid wages"
    elif "terminat" in text:
        primary_issue = "employment termination"
    elif domain == "unknown":
        primary_issue = None
    else:
        primary_issue = "general legal information request"

    secondary_issues = []
    if domain == "employment" and "terminat" in text and "paid" in text:
        secondary_issues = ["termination following complaint"]

    if "indian law" in text or "india" in text:
        jurisdiction: str | None = "India"
    elif "texas" in text:
        jurisdiction = "Texas, United States"
    elif "andhra pradesh" in text:
        jurisdiction = "Andhra Pradesh, India"
    else:
        jurisdiction = None

    parties = []
    name_match = re.search(r"landlord\s+([A-Z][a-zA-Z]+)", message)
    if "landlord" in text:
        parties = [
            {"role": "tenant", "name": None},
            {
                "role": "landlord",
                "name": name_match.group(1) if name_match else None,
            },
        ]
    elif "employer" in text or "employee" in text:
        parties = [
            {"role": "employee", "name": None},
            {"role": "employer", "name": None},
        ]

    if any(k in text for k in ("court tomorrow", "hearing tomorrow", "immediate danger")):
        urgency = "urgent"
    elif any(k in text for k in ("7 days", "notice", "deadline", "summons")):
        urgency = "time_sensitive"
    else:
        urgency = "normal"

    if any(k in text for k in _DISPUTE_KEYWORDS):
        intent = "dispute_resolution"
    else:
        intent = "general_information"

    missing_information = []
    if jurisdiction is None:
        missing_information.append("jurisdiction")
    if domain == "landlord_tenant":
        missing_information.extend(
            ["rental agreement terms", "reason given for withholding deposit"]
        )
    elif domain == "employment":
        missing_information.extend(["employment contract terms", "pay records"])

    clarification_questions = []
    if jurisdiction is None:
        clarification_questions.append("Which country/state does this matter concern?")
    if domain == "landlord_tenant":
        clarification_questions.extend(
            [
                "What does the rental agreement say about the deposit?",
                "Did the landlord provide a reason for withholding it?",
                "When did the tenancy end?",
            ]
        )
    elif domain == "employment":
        clarification_questions.extend(
            [
                "What does the employment contract say about pay?",
                "What pay records do you have for the unpaid period?",
            ]
        )

    return {
        "intent": intent,
        "legal_domain": domain,
        "primary_issue": primary_issue,
        "secondary_issues": secondary_issues,
        "jurisdiction": jurisdiction,
        "parties": parties,
        "facts": [f"User states: {message}"],
        "dates": sorted(set(_DATE_PATTERN.findall(text))),
        "amounts": _AMOUNT_PATTERN.findall(message),
        "missing_information": missing_information,
        "clarification_questions": clarification_questions[:5],
        "urgency": urgency,
        "confidence": 0.85,
        "prompt_version": "mock-v1",
    }
