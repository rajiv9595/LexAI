"""AI model definitions and data transfer contracts."""

from app.ai.models.query_understanding import (
    LegalIntent,
    LegalParty,
    LegalQueryUnderstanding,
    LegalDomain,
    QueryUrgency,
)
from app.ai.models.responses import (
    AIRequest,
    AIRequestMessage,
    AIResponse,
    LegalAssistantResponse,
    LegalReferenceItem,
    SafetyAssessment,
    SafetyFlag,
    SafetyStatus,
)

__all__ = [
    "AIRequest",
    "AIRequestMessage",
    "AIResponse",
    "LegalAssistantResponse",
    "LegalReferenceItem",
    "LegalIntent",
    "LegalParty",
    "LegalQueryUnderstanding",
    "LegalDomain",
    "QueryUrgency",
    "SafetyAssessment",
    "SafetyFlag",
    "SafetyStatus",
]
