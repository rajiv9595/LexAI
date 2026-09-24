"""Unit tests for Gemini AI Provider, provider factory, error mapping, and structured generation."""

import json
from unittest.mock import MagicMock, patch
import pytest
from google.genai import errors

from app.ai.models.responses import (
    AIRequest,
    AIRequestMessage,
    AIResponse,
    LegalAssistantResponse,
    SafetyStatus,
)
from app.ai.providers.base import MockDeterministicAIProvider
from app.ai.providers.factory import get_ai_provider
from app.ai.providers.gemini import (
    GeminiAIProvider,
    GeminiAuthenticationError,
    GeminiConfigurationError,
    GeminiError,
    GeminiRateLimitError,
    GeminiResponseError,
    GeminiTimeoutError,
)
from app.ai.services.assistant_orchestrator import AssistantOrchestrator
from app.core.config import Settings


class TestGeminiConfigurationAndFactory:
    """Test environment configuration and factory provider resolution."""

    def test_factory_returns_mock_when_ai_disabled(self):
        with patch("app.ai.providers.factory.settings.ai_enabled", False):
            provider = get_ai_provider()
            assert isinstance(provider, MockDeterministicAIProvider)
            assert provider.provider_name == "deterministic-mock"

    def test_factory_returns_mock_when_provider_is_mock(self):
        with patch("app.ai.providers.factory.settings.ai_enabled", True), patch(
            "app.ai.providers.factory.settings.ai_provider", "mock"
        ):
            provider = get_ai_provider()
            assert isinstance(provider, MockDeterministicAIProvider)

    def test_factory_raises_when_gemini_key_missing(self):
        with patch("app.ai.providers.factory.settings.ai_enabled", True), patch(
            "app.ai.providers.factory.settings.ai_provider", "gemini"
        ), patch("app.ai.providers.factory.settings.gemini_api_key", None):
            with pytest.raises(GeminiConfigurationError, match="Gemini API key is required"):
                get_ai_provider()

    def test_factory_raises_on_unknown_provider(self):
        with patch("app.ai.providers.factory.settings.ai_enabled", True), patch(
            "app.ai.providers.factory.settings.ai_provider", "unsupported_provider"
        ):
            with pytest.raises(GeminiConfigurationError, match="Unsupported AI provider"):
                get_ai_provider()

    def test_factory_returns_gemini_when_configured(self):
        mock_client = MagicMock()
        with patch("app.ai.providers.factory.settings.ai_enabled", True), patch(
            "app.ai.providers.factory.settings.ai_provider", "gemini"
        ), patch("app.ai.providers.factory.settings.gemini_api_key", "test-key"), patch(
            "app.ai.providers.gemini.genai.Client", return_value=mock_client
        ):
            provider = get_ai_provider()
            assert isinstance(provider, GeminiAIProvider)
            assert provider.provider_name == "gemini"


class TestGeminiAIProviderExecution:
    """Test Gemini provider generation, structured parsing, and exception mapping using mocked SDK."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        return client

    @pytest.fixture
    def valid_structured_json(self):
        return json.dumps({
            "answer": "A security deposit is a refundable sum paid to protect against property damage.",
            "issue_summary": "Inquiry regarding security deposit fundamentals in residential leasing.",
            "assumptions": ["Standard residential tenancy agreement"],
            "missing_information": ["Applicable state jurisdiction"],
            "potential_considerations": ["Statutory timelines for deposit return"],
            "suggested_next_steps": ["Inspect the property and retain receipts"],
            "references": [],
            "disclaimer": "Informational only.",
            "prompt_version": "v1",
            "provider_used": "gemini",
        })

    def test_successful_structured_generation(self, mock_client, valid_structured_json):
        mock_response = MagicMock()
        mock_response.text = valid_structured_json
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=120,
            candidates_token_count=85,
        )
        mock_client.models.generate_content.return_value = mock_response

        provider = GeminiAIProvider(
            api_key="test-key", model_name="gemini-2.5-flash", client=mock_client
        )
        request = AIRequest(
            system_instruction="You are a legal assistant.",
            user_message="What is a security deposit?",
            conversation_history=[
                AIRequestMessage(role="user", content="Hi"),
                AIRequestMessage(role="assistant", content="Hello"),
            ],
            case_context={"tier": "standard"},
            retrieved_context=[],
        )

        ai_response = provider.generate(request)

        assert isinstance(ai_response, AIResponse)
        assert ai_response.provider == "gemini"
        # Explicitly configured model names pass through verbatim (never rewritten).
        assert ai_response.model == "gemini-2.5-flash"
        assert ai_response.prompt_tokens == 120
        assert ai_response.completion_tokens == 85
        assert "security deposit" in ai_response.content

        # Verify SDK was called with structured configuration
        mock_client.models.generate_content.assert_called_once()
        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert call_kwargs["config"].response_mime_type == "application/json"

    def test_malformed_json_raises_gemini_response_error(self, mock_client):
        mock_response = MagicMock()
        mock_response.text = "NOT VALID JSON"
        mock_client.models.generate_content.return_value = mock_response

        provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with pytest.raises(GeminiResponseError, match="not valid structured JSON"):
            provider.generate(request)

    def test_empty_response_raises_gemini_response_error(self, mock_client):
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client.models.generate_content.return_value = mock_response

        provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with pytest.raises(GeminiResponseError, match="empty response"):
            provider.generate(request)

    def test_auth_error_mapping(self, mock_client):
        api_error = errors.APIError(401, "API_KEY_INVALID: API key not valid. Please pass a valid API key.")
        mock_client.models.generate_content.side_effect = api_error

        provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with pytest.raises(GeminiAuthenticationError, match="invalid or unauthorized API key"):
            provider.generate(request)

    def test_rate_limit_error_mapping(self, mock_client):
        api_error = errors.APIError(429, "RESOURCE_EXHAUSTED: Quota exceeded for quota metric.")
        mock_client.models.generate_content.side_effect = api_error

        provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with pytest.raises(GeminiRateLimitError, match="rate limit or quota exceeded"):
            provider.generate(request)

    def test_timeout_error_mapping(self, mock_client):
        api_error = errors.APIError(408, "DEADLINE_EXCEEDED: Request timed out.")
        mock_client.models.generate_content.side_effect = api_error

        provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with pytest.raises(GeminiTimeoutError, match="timed out"):
            provider.generate(request)

    def test_model_unavailable_maps_to_configuration_error(self, mock_client):
        api_error = errors.APIError(404, "NOT_FOUND: This model is no longer available.")
        mock_client.models.generate_content.side_effect = api_error

        provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with pytest.raises(GeminiConfigurationError, match="not available"):
            provider.generate(request)


class TestOrchestratorWithGemini:
    """Test end-to-end orchestration with Gemini provider."""

    def test_orchestrator_parses_gemini_structured_json(self):
        mock_client = MagicMock()
        # Pipeline now makes two provider calls: understanding, then final answer.
        mock_understanding = MagicMock()
        mock_understanding.text = json.dumps({
            "intent": "dispute_resolution",
            "legal_domain": "contract",
            "primary_issue": "lease termination",
            "secondary_issues": [],
            "jurisdiction": None,
            "parties": [],
            "facts": ["User states tenancy termination is sought."],
            "dates": [],
            "amounts": [],
            "missing_information": ["jurisdiction"],
            "clarification_questions": [],
            "urgency": "normal",
            "confidence": 0.8,
        })
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "answer": "A lease termination requires proper statutory written notice.",
            "issue_summary": "Residential lease termination query",
            "assumptions": ["Periodic month-to-month tenancy"],
            "missing_information": ["Whether lease is fixed term or month to month"],
            "potential_considerations": ["30-day notice requirement under local law"],
            "suggested_next_steps": ["Check lease clause section on notices"],
            "references": [],
        })
        mock_client.models.generate_content.side_effect = [
            mock_understanding,
            mock_response,
        ]

        gemini_provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        orchestrator = AssistantOrchestrator(provider=gemini_provider)

        result = orchestrator.process_query("How do I terminate my rental agreement?")

        assert isinstance(result, LegalAssistantResponse)
        assert result.answer == "A lease termination requires proper statutory written notice."
        assert result.issue_summary == "Residential lease termination query"
        assert len(result.potential_considerations) == 1
        assert result.provider_used == "gemini"
        assert result.safety_assessment.status == SafetyStatus.SAFE
        assert result.prompt_version == "v1"

    def test_grounding_rule_empty_retrieved_context_clears_references(self):
        mock_client = MagicMock()
        mock_understanding = MagicMock()
        mock_understanding.text = json.dumps({
            "intent": "general_information",
            "legal_domain": "unknown",
            "primary_issue": None,
            "urgency": "normal",
            "confidence": 0.5,
        })
        mock_response = MagicMock()
        # Even if Gemini hallucinated a reference, orchestrator clears it when retrieved_context is empty
        mock_response.text = json.dumps({
            "answer": "Answer text.",
            "references": [{"title": "Fabricated Case v. Authority", "kind": "Case"}],
        })
        mock_client.models.generate_content.side_effect = [
            mock_understanding,
            mock_response,
        ]

        gemini_provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        orchestrator = AssistantOrchestrator(provider=gemini_provider)

        result = orchestrator.process_query(
            user_message="Tell me a case",
            retrieved_context=[],  # Empty grounding context
        )

        assert result.references == []  # Hallucinated citation stripped!

    def test_escalation_bypasses_gemini_provider(self):
        mock_client = MagicMock()
        gemini_provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        orchestrator = AssistantOrchestrator(provider=gemini_provider)

        result = orchestrator.process_query("I am in immediate danger of physical violence!")

        assert result.safety_assessment.status == SafetyStatus.ESCALATE
        assert "URGENT:" in result.answer
        # Verify Gemini was NEVER called for an emergency escalation
        mock_client.models.generate_content.assert_not_called()

    def test_api_key_not_leaked_in_exceptions(self):
        secret_key = "AIzaSySecretApiKey123456789"
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = errors.APIError(401, f"Bad key {secret_key}")

        provider = GeminiAIProvider(api_key=secret_key, client=mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with pytest.raises(GeminiAuthenticationError) as exc_info:
            provider.generate(request)

        # Ensure sanitized error does not reveal the secret key
        assert secret_key not in str(exc_info.value)

    def test_503_spike_retried_once_then_succeeds(self):
        """STEP 43: a transient 503 gets exactly one bounded retry, then succeeds."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"answer": "Deposit guidance."})
        mock_response.usage_metadata = None
        mock_client.models.generate_content.side_effect = [
            errors.APIError(503, "UNAVAILABLE: model under high demand."),
            mock_response,
        ]
        provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with patch("app.ai.providers.gemini.time.sleep") as mock_sleep:
            ai_response = provider.generate(request)

        assert "Deposit guidance." in ai_response.content
        assert mock_client.models.generate_content.call_count == 2
        mock_sleep.assert_called_once_with(1.0)

    def test_persistent_503_raises_safe_error_without_retry_storm(self):
        """STEP 43: a sustained 503 yields one retry only, then a sanitized error."""
        secret_key = "AIzaSySecretApiKey123456789"
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = errors.APIError(
            503, f"UNAVAILABLE: spike ({secret_key})."
        )
        provider = GeminiAIProvider(api_key=secret_key, client=mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with patch("app.ai.providers.gemini.time.sleep"):
            with pytest.raises(GeminiResponseError) as exc_info:
                provider.generate(request)

        # Bounded: initial attempt plus exactly one retry — never a loop.
        assert mock_client.models.generate_content.call_count == 2
        # Sanitized: no key material in the raised message.
        assert secret_key not in str(exc_info.value)


def _failover_success_payload(answer="Lease deposit guidance."):
    """Build a mock SDK response satisfying the legal_assistant contract."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({"answer": answer})
    mock_response.usage_metadata = None
    return mock_response


def _failover_provider(mock_client, chain=("gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.8-flash")):
    """Build a failover provider with an explicit model chain for testing."""
    primary, *fallbacks = chain
    return GeminiAIProvider(
        api_key="test-key",
        model_name=primary,
        fallback_models=list(fallbacks),
        client=mock_client,
    )


def _attempted_models(mock_client):
    """Return the ordered model names used across generate_content calls."""
    return [
        call.kwargs.get("model")
        for call in mock_client.models.generate_content.call_args_list
    ]


class TestGeminiModelFailover:
    """Failover across configured Gemini models for transient conditions."""

    def test_primary_success_no_fallback(self):
        """TEST 1: 3.6 succeeds — exactly one call, no fallback."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = _failover_success_payload()
        provider = _failover_provider(mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        response = provider.generate(request)

        assert "Lease deposit guidance." in response.content
        assert response.model == "gemini-3.6-flash"
        assert mock_client.models.generate_content.call_count == 1

    def test_429_fails_over_to_next_model_once(self):
        """TEST 2: 3.6 -> 429, 3.5 -> success; 3.7 never called."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            errors.APIError(429, "RESOURCE_EXHAUSTED: quota exceeded."),
            _failover_success_payload(),
        ]
        provider = _failover_provider(mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        response = provider.generate(request)

        assert "Lease deposit guidance." in response.content
        assert response.model == "gemini-3.5-flash"
        assert _attempted_models(mock_client) == ["gemini-3.6-flash", "gemini-3.5-flash"]

    def test_503_fails_over_to_next_model(self):
        """TEST 3: 3.6 -> 503, 3.5 -> success."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            errors.APIError(503, "UNAVAILABLE: model under high demand."),
            _failover_success_payload(),
        ]
        provider = _failover_provider(mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        response = provider.generate(request)

        assert "Lease deposit guidance." in response.content
        assert response.model == "gemini-3.5-flash"
        assert _attempted_models(mock_client) == ["gemini-3.6-flash", "gemini-3.5-flash"]

    def test_two_failures_then_success(self):
        """TEST 4: 3.6 -> 429, 3.5 -> 429, 3.7 -> success (3 attempts)."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            errors.APIError(429, "RESOURCE_EXHAUSTED: quota exceeded."),
            errors.APIError(429, "RESOURCE_EXHAUSTED: quota exceeded."),
            _failover_success_payload(),
        ]
        provider = _failover_provider(mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        response = provider.generate(request)

        assert response.model == "gemini-3.7-flash"
        assert _attempted_models(mock_client) == [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.7-flash",
        ]

    def test_full_chain_exhaustion_raises_without_loop(self):
        """TEST 5: all four fail — exactly four attempts, safe terminal error."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            errors.APIError(429, "RESOURCE_EXHAUSTED: quota exceeded."),
            errors.APIError(503, "UNAVAILABLE: model under high demand."),
            errors.APIError(503, "UNAVAILABLE: model under high demand."),
            errors.APIError(429, "RESOURCE_EXHAUSTED: quota exceeded."),
        ]
        provider = _failover_provider(mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with pytest.raises(GeminiError) as exc_info:
            provider.generate(request)

        assert _attempted_models(mock_client) == [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.7-flash",
            "gemini-3.8-flash",
        ]
        assert mock_client.models.generate_content.call_count == 4
        assert isinstance(exc_info.value, (GeminiRateLimitError, GeminiResponseError))

    def test_404_model_unavailable_fails_over(self):
        """TEST 6: 3.6 -> 404 model unavailable, 3.5 -> success (no retry of 3.6)."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            errors.APIError(404, "NOT_FOUND: model gemini-3.6-flash is not found."),
            _failover_success_payload(),
        ]
        provider = _failover_provider(mock_client)
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        response = provider.generate(request)

        assert response.model == "gemini-3.5-flash"
        assert _attempted_models(mock_client) == ["gemini-3.6-flash", "gemini-3.5-flash"]

    def test_authentication_error_does_not_fail_over(self):
        """TEST 7: auth failure raises safely without trying fallback models."""
        secret_key = "AIzaSySecretApiKey123456789"
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = errors.APIError(
            401, "Unauthorized: invalid API key."
        )
        provider = GeminiAIProvider(
            api_key=secret_key,
            model_name="gemini-3.6-flash",
            fallback_models=["gemini-3.5-flash", "gemini-3.7-flash"],
            client=mock_client,
        )
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with pytest.raises(GeminiAuthenticationError) as exc_info:
            provider.generate(request)

        assert mock_client.models.generate_content.call_count == 1
        assert secret_key not in str(exc_info.value)

    def test_two_calls_fail_over_independently(self):
        """TEST 8: understanding succeeds on 3.6; final answer fails over to 3.5."""
        mock_client = MagicMock()
        understanding_payload = MagicMock()
        understanding_payload.text = json.dumps(
            {"intent": "general_information", "legal_domain": "contract"}
        )
        understanding_payload.usage_metadata = None
        mock_client.models.generate_content.side_effect = [
            understanding_payload,
            errors.APIError(429, "RESOURCE_EXHAUSTED: quota exceeded."),
            _failover_success_payload(),
        ]
        provider = _failover_provider(mock_client)

        understanding_request = AIRequest(
            system_instruction="Understand",
            user_message="Review my lease deposit clause.",
            response_schema_name="query_understanding",
        )
        understanding = provider.generate(understanding_request)
        assert understanding.model == "gemini-3.6-flash"

        answer_request = AIRequest(system_instruction="Answer", user_message="Review my lease deposit clause.")
        answer = provider.generate(answer_request)
        assert answer.model == "gemini-3.5-flash"

        assert _attempted_models(mock_client) == [
            "gemini-3.6-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
        ]

    def test_chain_exhaustion_is_safe_and_bounded(self):
        """TEST 9: all models fail — safe error, no secret leak, no retry storm."""
        secret_key = "AIzaSySecretApiKey123456789"
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = errors.APIError(
            429, "RESOURCE_EXHAUSTED: quota exceeded."
        )
        provider = GeminiAIProvider(
            api_key=secret_key,
            model_name="gemini-3.6-flash",
            fallback_models=["gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.8-flash"],
            client=mock_client,
        )
        request = AIRequest(system_instruction="Prompt", user_message="Query")

        with pytest.raises(GeminiRateLimitError) as exc_info:
            provider.generate(request)

        assert mock_client.models.generate_content.call_count == 4
        assert secret_key not in str(exc_info.value)

    def test_2_5_flash_never_in_fallback_chain(self):
        """gemini-2.5-flash (404 in live test) is always excluded from failover."""
        mock_client = MagicMock()
        provider = GeminiAIProvider(
            api_key="test-key",
            model_name="gemini-3.6-flash",
            fallback_models=["gemini-2.5-flash", "gemini-3.5-flash"],
            client=mock_client,
        )
        assert "gemini-2.5-flash" not in provider.model_chain
        assert provider.model_chain == ["gemini-3.6-flash", "gemini-3.5-flash"]

    def test_factory_wires_configured_fallback_chain(self):
        """Factory builds the failover provider from GEMINI_MODEL settings."""
        mock_client = MagicMock()
        with patch(
            "app.ai.providers.factory.settings.gemini_model", "gemini-3.6-flash"
        ), patch(
            "app.ai.providers.factory.settings.gemini_fallback_models",
            "gemini-3.5-flash,gemini-3.7-flash,gemini-3.8-flash",
        ), patch(
            "app.ai.providers.gemini.genai.Client", return_value=mock_client
        ):
            provider = get_ai_provider(provider_name="gemini")
        assert isinstance(provider, GeminiAIProvider)
        assert provider.model_chain == [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.7-flash",
            "gemini-3.8-flash",
        ]
