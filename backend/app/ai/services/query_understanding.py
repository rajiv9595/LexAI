"""Legal query understanding service: structural analysis before final answers."""

import json
import logging

from pydantic import ValidationError

from app.ai.models.query_understanding import LegalQueryUnderstanding
from app.ai.models.responses import AIRequest, AIRequestMessage, SafetyStatus
from app.ai.prompts.query_understanding import (
    LEGAL_QUERY_UNDERSTANDING_PROMPT_VERSION,
    LEGAL_QUERY_UNDERSTANDING_SYSTEM_PROMPT,
)
from app.ai.providers.base import AIProvider
from app.ai.providers.factory import get_ai_provider
from app.ai.providers.gemini import GeminiResponseError
from app.ai.safety.guardrails import assess_request

logger = logging.getLogger(__name__)


class QueryUnderstandingService:
    """Produces a LegalQueryUnderstanding for a user message.

    Uses the existing safety assessment (authoritative) and the configured
    AI provider. ESCALATE requests never reach the provider: a minimal
    understanding is returned instead. No legal references are produced;
    this step performs extraction only.
    """

    def __init__(
        self,
        provider: AIProvider | None = None,
        provider_name: str | None = None,
    ):
        self.provider = provider or get_ai_provider(provider_name)

    def understand(
        self,
        user_message: str,
        conversation_history: list[AIRequestMessage] | None = None,
    ) -> LegalQueryUnderstanding:
        """Analyze a user message into structured query understanding."""
        normalized_message = user_message.strip()

        # Existing safety assessment remains authoritative.
        safety = assess_request(normalized_message)
        if safety.status == SafetyStatus.ESCALATE:
            logger.info("Query understanding short-circuited on ESCALATE assessment")
            return LegalQueryUnderstanding(
                intent="other",
                legal_domain="unknown",
                primary_issue=None,
                urgency="urgent",
                confidence=0.5,
                prompt_version=LEGAL_QUERY_UNDERSTANDING_PROMPT_VERSION,
            )

        ai_request = AIRequest(
            system_instruction=LEGAL_QUERY_UNDERSTANDING_SYSTEM_PROMPT,
            user_message=normalized_message,
            conversation_history=conversation_history or [],
            temperature=0.0,
            max_tokens=2048,
            response_schema_name="query_understanding",
        )

        raw_response = self.provider.generate(ai_request)

        content = (raw_response.content or "").strip()
        if not content:
            raise GeminiResponseError("Query understanding returned an empty response.")

        try:
            parsed = json.loads(content)
            understanding = LegalQueryUnderstanding.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
            logger.error("Query understanding output failed structured validation")
            raise GeminiResponseError(
                "Query understanding response was not valid structured data."
            ) from exc

        understanding.prompt_version = LEGAL_QUERY_UNDERSTANDING_PROMPT_VERSION
        logger.info(
            "Query understanding completed (message_chars=%d, domain=%s)",
            len(normalized_message),
            understanding.legal_domain,
        )
        return understanding
