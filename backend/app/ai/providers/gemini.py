"""Google Gemini AI Provider implementing structured legal generation."""

import json
import logging
import time
from typing import Any

from google import genai
from google.genai import errors, types

from app.ai.models.query_understanding import LegalQueryUnderstanding
from app.ai.models.responses import (
    AIRequest,
    AIResponse,
    LegalAssistantResponse,
    SafetyStatus,
)
from app.ai.providers.base import AIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

# Structured output tasks supported through the single provider abstraction.
RESPONSE_SCHEMAS = {
    "legal_assistant": LegalAssistantResponse,
    "query_understanding": LegalQueryUnderstanding,
}


class GeminiError(Exception):
    """Base exception for Gemini provider operations."""


class GeminiConfigurationError(GeminiError):
    """Raised when Gemini credentials or settings are missing or invalid."""


class GeminiAuthenticationError(GeminiError):
    """Raised when the Gemini API key is rejected or unauthorized."""


class GeminiRateLimitError(GeminiError):
    """Raised when the Gemini API rate limit or quota is exceeded."""


class GeminiTimeoutError(GeminiError):
    """Raised when a request to Gemini times out."""


class GeminiResponseError(GeminiError):
    """Raised when Gemini returns a malformed or unusable response."""


class GeminiAIProvider(AIProvider):
    """Provider adapter communicating with Google Gemini via the official GenAI SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        model: str | None = None,
        client: genai.Client | None = None,
    ):
        self._api_key = api_key or settings.gemini_api_key
        # The configured model is used verbatim; never rewritten.
        self._model_name = (
            model_name or model or settings.gemini_model or "gemini-3.6-flash"
        )

        if not self._api_key or not self._api_key.strip():
            raise GeminiConfigurationError(
                "Gemini API key is required but not configured in settings."
            )

        # Allow passing an existing client for testing/mocking
        self._client = client or genai.Client(api_key=self._api_key)

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, request: AIRequest) -> AIResponse:
        """Execute structured generation using Google Gemini."""
        schema_name = request.response_schema_name or "legal_assistant"
        response_schema = RESPONSE_SCHEMAS.get(schema_name)
        if response_schema is None:
            raise GeminiConfigurationError(
                f"Unsupported structured response schema: '{schema_name}'."
            )

        # 1. Prepare conversation contents
        contents = self._build_contents(request)

        # 2. Build configuration with structured schema
        formatting_rules = [
            f"{request.system_instruction}\n\n"
            "CRITICAL FORMATTING INSTRUCTIONS:\n"
            "1. Output MUST strictly match the required JSON schema."
        ]
        if schema_name == "legal_assistant":
            formatting_rules.append(
                "2. If retrieved_context is empty, 'references' MUST be an empty list [].\n"
                "3. Each entry in 'references' MUST carry a 'source_id' copied verbatim from the supplied retrieved context; do NOT invent source IDs, statutes, citations, case law, or URLs.\n"
                "4. Retrieved material may be prototype research records: never present them as verified legal authority.\n"
                "5. Clearly communicate that LexAssist provides legal information, not formal advice."
            )
        system_instruction_text = "\n".join(formatting_rules)

        config = types.GenerateContentConfig(
            system_instruction=system_instruction_text,
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            response_mime_type="application/json",
            response_schema=response_schema,
        )

        # 3. Dispatch generation call with bounded exception mapping (max 1 retry for 503 transient spike)
        response = None
        for attempt in range(2):
            try:
                response = self._client.models.generate_content(
                    model=self._model_name,
                    contents=contents,
                    config=config,
                )
                break
            except errors.APIError as exc:
                status_code = getattr(exc, "code", None)
                message = str(exc).lower()
                if status_code == 503 and attempt == 0:
                    logger.info("Gemini 503 spike encountered; retrying once after 1s...")
                    time.sleep(1.0)
                    continue

                if status_code in (401, 403) or "unauthorized" in message or (
                    "api_key" in message
                    or ("invalid argument" in message and "key" in message)
                ):
                    logger.error("Gemini provider authentication failure (status=%s)", status_code)
                    raise GeminiAuthenticationError("Gemini authentication failed: invalid or unauthorized API key.") from exc
                elif status_code == 404 or "not_found" in message or "is no longer available" in message:
                    logger.error("Gemini model unavailable (status=%s)", status_code)
                    raise GeminiConfigurationError("The configured Gemini model is not available. Check GEMINI_MODEL configuration.") from exc
                elif status_code == 429 or "resource_exhausted" in message or "quota" in message or "rate" in message:
                    logger.warning("Gemini provider rate limit or quota reached (status=%s)", status_code)
                    raise GeminiRateLimitError("Gemini rate limit or quota exceeded. Please retry shortly.") from exc
                elif status_code == 408 or "timeout" in message or "deadline_exceeded" in message:
                    logger.warning("Gemini provider request timeout")
                    raise GeminiTimeoutError("Gemini request timed out.") from exc
                else:
                    logger.error("Gemini API error (status=%s)", status_code)
                    raise GeminiResponseError(f"Gemini generation error: {getattr(exc, 'message', 'unknown API error')}") from exc
            except TimeoutError as exc:
                logger.warning("Gemini network request timeout")
                raise GeminiTimeoutError("Gemini request timed out.") from exc
            except Exception as exc:
                logger.error("Unexpected error during Gemini generation")
                raise GeminiResponseError("Unexpected error communicating with Gemini provider.") from exc

        # 4. Parse and validate response content
        raw_text = response.text or ""
        if not raw_text.strip():
            raise GeminiResponseError("Gemini returned an empty response.")

        # Validate that output parses as valid JSON matching our contract
        try:
            parsed_json = json.loads(raw_text)
            if not isinstance(parsed_json, dict):
                raise ValueError("Response is not a JSON object")
            if schema_name == "legal_assistant" and not str(
                parsed_json.get("answer") or ""
            ).strip():
                raise ValueError("Response is missing the required 'answer' field")
        except Exception as exc:
            logger.error("Gemini structured output failed JSON decoding")
            raise GeminiResponseError("Gemini response was not valid structured JSON.") from exc

        # 5. Extract token usage metadata if available
        prompt_tokens = None
        completion_tokens = None
        usage = getattr(response, "usage_metadata", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_token_count", None)
            completion_tokens = getattr(usage, "candidates_token_count", None)

        return AIResponse(
            content=raw_text,
            provider=self.provider_name,
            model=self._model_name,
            finish_reason="stop",
            safety_status=SafetyStatus.SAFE,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    def _build_contents(self, request: AIRequest) -> list[Any]:
        """Convert an AIRequest into conversation turns suitable for Gemini."""
        turns: list[Any] = []

        # Include prior conversation history
        for msg in request.conversation_history:
            role = "user" if msg.role == "user" else "model"
            turns.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content)],
                )
            )

        # Build current user prompt with context annotations
        prompt_parts: list[str] = []

        if request.query_understanding:
            prompt_parts.append(
                "[Legal Query Understanding (AI-derived interpretation of the "
                "user's message, not verified facts — rely primarily on the "
                "original user message):\n"
                f"{request.query_understanding}\n]"
            )

        if request.case_context:
            context_summary = ", ".join(f"{k}: {v}" for k, v in request.case_context.items())
            prompt_parts.append(f"[User/Case Context: {context_summary}]")

        if request.retrieved_context:
            grounding_text = "\n".join(f"- {c}" for c in request.retrieved_context)
            prompt_parts.append(
                "[Retrieved Legal Context (curated prototype research records; "
                "not verified legal authority — do not present as official law):\n"
                f"{grounding_text}\n]"
            )
        else:
            prompt_parts.append("[Retrieved Legal Context: None available. Do not cite external cases or statutes.]")

        prompt_parts.append(request.user_message)
        full_user_text = "\n\n".join(prompt_parts)

        turns.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=full_user_text)],
            )
        )

        return turns
