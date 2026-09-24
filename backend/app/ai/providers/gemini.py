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

# Models that must never be used as automatic fallbacks.
# gemini-2.5-flash returned 404 model-unavailable in the controlled live
# test and is therefore excluded from production failover.
EXCLUDED_FALLBACK_MODELS = {"gemini-2.5-flash"}


def resolve_model_chain(
    primary: str, fallback_models: Any | None = None
) -> list[str]:
    """Build the ordered model attempt chain for one logical generation.

    - ``primary`` is always attempted first.
    - ``fallback_models`` may be a comma-separated string or a sequence.
    - Duplicates of the primary, blanks, and excluded models
      (e.g. gemini-2.5-flash) are dropped while preserving order.
    - Each model is attempted at most once per logical request; the
      caller never loops back.
    """
    chain: list[str] = []
    if primary and str(primary).strip():
        chain.append(str(primary).strip())
    candidates: list[str] = []
    if isinstance(fallback_models, str):
        candidates = fallback_models.split(",")
    elif fallback_models:
        candidates = list(fallback_models)
    for candidate in candidates:
        name = str(candidate or "").strip()
        if not name:
            continue
        if name in chain:
            continue
        if name.lower() in EXCLUDED_FALLBACK_MODELS:
            logger.warning(
                "Gemini fallback model excluded: model=%s reason=excluded_2_5_flash",
                name,
            )
            continue
        chain.append(name)
    return chain


def _failover_category(exc: errors.APIError) -> str | None:
    """Classify an API error for failover.

    Returns 'rate_limited', 'service_unavailable', or 'model_unavailable'
    when the next configured model may be attempted, else None.
    Mirrors the classification order used by the single-model path.
    """
    status_code = getattr(exc, "code", None)
    message = str(exc).lower()
    if status_code == 503 or "service_unavailable" in message or "unavailable" in message:
        return "service_unavailable"
    if (
        status_code == 429
        or "resource_exhausted" in message
        or "quota" in message
        or "rate" in message
        or "too_many_requests" in message
    ):
        return "rate_limited"
    if (
        status_code == 404
        or "not_found" in message
        or "is no longer available" in message
    ):
        return "model_unavailable"
    return None


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
        fallback_models: Any | None = None,
        fallback_model_names: Any | None = None,
    ):
        self._api_key = api_key or settings.gemini_api_key
        # The configured model is used verbatim; never rewritten.
        self._model_name = (
            model_name or model or settings.gemini_model or "gemini-3.6-flash"
        )

        # Ordered failover chain. Direct construction defaults to the
        # single primary model (legacy behavior); the provider factory
        # wires the configured GEMINI_FALLBACK_MODELS for production.
        requested = (
            fallback_models
            if fallback_models is not None
            else fallback_model_names
        )
        self._fallback_models = tuple(
            resolve_model_chain(self._model_name, requested)[1:]
        )
        self._model_chain = [self._model_name, *self._fallback_models]

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

    @property
    def fallback_models(self) -> tuple[str, ...]:
        """Configured fallback models, excluding the primary."""
        return self._fallback_models

    @property
    def model_chain(self) -> list[str]:
        """Ordered models attempted per logical generation (primary first)."""
        return list(self._model_chain)

    def generate(self, request: AIRequest) -> AIResponse:
        """Execute structured generation using Google Gemini.

        Single-model providers keep the legacy bounded behavior (one 503
        spike retry). Providers with configured fallbacks attempt each
        model at most once, failing over only on 429 / 503 / 404-model-
        unavailable (or an unsatisfiable structured-output contract) and
        stopping at the first success. Each generate() call fails over
        independently, so Legal Query Understanding and the final answer
        may legitimately use different models.
        """
        schema_name = request.response_schema_name or "legal_assistant"
        response_schema = RESPONSE_SCHEMAS.get(schema_name)
        if response_schema is None:
            raise GeminiConfigurationError(
                f"Unsupported structured response schema: '{schema_name}'."
            )

        # 1. Prepare conversation contents (identical for every attempt)
        contents = self._build_contents(request)

        # 2. Build configuration with structured schema (identical per model)
        config = self._build_generation_config(request, schema_name, response_schema)

        if len(self._model_chain) <= 1:
            return self._generate_single_model(request, schema_name, contents, config)
        return self._generate_with_failover(request, schema_name, contents, config)

    def _build_generation_config(
        self, request: AIRequest, schema_name: str, response_schema: Any
    ) -> Any:
        """Build the structured-output generation config (shared by all models)."""
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

        return types.GenerateContentConfig(
            system_instruction=system_instruction_text,
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            response_mime_type="application/json",
            response_schema=response_schema,
        )

    @staticmethod
    def _map_api_error(exc: errors.APIError) -> GeminiError:
        """Map a raw GenAI API error to a sanitized provider exception."""
        status_code = getattr(exc, "code", None)
        message = str(exc).lower()
        if status_code in (401, 403) or "unauthorized" in message or (
            "api_key" in message
            or ("invalid argument" in message and "key" in message)
        ):
            logger.error("Gemini provider authentication failure (status=%s)", status_code)
            return GeminiAuthenticationError("Gemini authentication failed: invalid or unauthorized API key.")
        elif status_code == 404 or "not_found" in message or "is no longer available" in message:
            logger.error("Gemini model unavailable (status=%s)", status_code)
            return GeminiConfigurationError("The configured Gemini model is not available. Check GEMINI_MODEL configuration.")
        elif status_code == 429 or "resource_exhausted" in message or "quota" in message or "rate" in message:
            logger.warning("Gemini provider rate limit or quota reached (status=%s)", status_code)
            return GeminiRateLimitError("Gemini rate limit or quota exceeded. Please retry shortly.")
        elif status_code == 408 or "timeout" in message or "deadline_exceeded" in message:
            logger.warning("Gemini provider request timeout")
            return GeminiTimeoutError("Gemini request timed out.")
        else:
            logger.error("Gemini API error (status=%s)", status_code)
            return GeminiResponseError(f"Gemini generation error: {getattr(exc, 'message', 'unknown API error')}")

    def _parse_model_response(self, response: Any, schema_name: str) -> str:
        """Validate structured output and return the raw text.

        Raises GeminiResponseError when the model did not satisfy the
        required structured-output contract.
        """
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
        return raw_text

    @staticmethod
    def _extract_usage(response: Any) -> tuple[Any, Any]:
        """Extract token usage metadata if available."""
        prompt_tokens = None
        completion_tokens = None
        usage = getattr(response, "usage_metadata", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_token_count", None)
            completion_tokens = getattr(usage, "candidates_token_count", None)
        return prompt_tokens, completion_tokens

    def _build_success_response(self, raw_text: str, model: str, response: Any) -> AIResponse:
        """Assemble the provider response tagged with the model that succeeded."""
        prompt_tokens, completion_tokens = self._extract_usage(response)
        return AIResponse(
            content=raw_text,
            provider=self.provider_name,
            model=model,
            finish_reason="stop",
            safety_status=SafetyStatus.SAFE,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    def _generate_single_model(
        self, request: AIRequest, schema_name: str, contents: list[Any], config: Any
    ) -> AIResponse:
        """Legacy single-model generation (unchanged bounded behavior)."""
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

                raise self._map_api_error(exc) from exc
            except TimeoutError as exc:
                logger.warning("Gemini network request timeout")
                raise GeminiTimeoutError("Gemini request timed out.") from exc
            except Exception as exc:
                logger.error("Unexpected error during Gemini generation")
                raise GeminiResponseError("Unexpected error communicating with Gemini provider.") from exc

        # 4. Parse and validate response content
        raw_text = self._parse_model_response(response, schema_name)

        # 5. Extract token usage metadata if available
        return self._build_success_response(raw_text, self._model_name, response)

    def _generate_with_failover(
        self, request: AIRequest, schema_name: str, contents: list[Any], config: Any
    ) -> AIResponse:
        """Attempt each configured model once; stop at the first success."""
        last_error: GeminiError | None = None
        for model in self._model_chain:
            logger.info("Gemini model attempt: model=%s", model)
            try:
                response = self._client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
            except errors.APIError as exc:
                status_code = getattr(exc, "code", None)
                category = _failover_category(exc)
                if category is not None:
                    if category == "model_unavailable":
                        logger.warning(
                            "MODEL_UNAVAILABLE model=%s status=%s; continuing to next model",
                            model,
                            status_code,
                        )
                    else:
                        logger.warning(
                            "Gemini model failed: model=%s status=%s category=%s; continuing to next model",
                            model,
                            status_code,
                            category,
                        )
                    last_error = self._map_api_error(exc)
                    continue
                raise self._map_api_error(exc) from exc
            except TimeoutError as exc:
                logger.warning("Gemini network request timeout")
                raise GeminiTimeoutError("Gemini request timed out.") from exc
            except Exception as exc:
                logger.error("Unexpected error during Gemini generation")
                raise GeminiResponseError("Unexpected error communicating with Gemini provider.") from exc

            try:
                raw_text = self._parse_model_response(response, schema_name)
            except GeminiResponseError as exc:
                logger.warning(
                    "Gemini model failed structured contract: model=%s; continuing to next model",
                    model,
                )
                last_error = exc
                continue

            logger.info("Gemini generation succeeded: model=%s", model)
            return self._build_success_response(raw_text, model, response)

        logger.error("Gemini failover chain exhausted without success")
        if last_error is not None:
            raise last_error
        raise GeminiResponseError("Gemini generation failed on all configured models.")

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
