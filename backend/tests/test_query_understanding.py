"""Focused tests for Step 18 legal query understanding / issue extraction.

All tests run offline through the deterministic mock provider or a mocked
Gemini SDK client. No test requires real Gemini API access.
"""

import json
from typing import get_args
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.ai.models.query_understanding import (
    LegalDomain,
    LegalIntent,
    LegalQueryUnderstanding,
)
from app.ai.models.responses import SafetyStatus
from app.ai.prompts.query_understanding import (
    LEGAL_QUERY_UNDERSTANDING_PROMPT_VERSION,
)
from app.ai.providers.base import MockDeterministicAIProvider
from app.ai.providers.gemini import (
    GeminiAIProvider,
    GeminiConfigurationError,
    GeminiResponseError,
)
from app.ai.safety.guardrails import assess_request
from app.ai.services.assistant_orchestrator import AssistantOrchestrator
from app.ai.services.query_understanding import QueryUnderstandingService


def understand_with_mock(message: str) -> LegalQueryUnderstanding:
    service = QueryUnderstandingService(
        provider=MockDeterministicAIProvider()
    )
    return service.understand(message)


class TestBasicClassification:
    """A. Basic classification."""

    def test_security_deposit_question_classification(self):
        result = understand_with_mock(
            "What is a security deposit in a rental agreement?"
        )
        assert result.legal_domain == "landlord_tenant"
        assert result.intent == "general_information"


class TestFactExtraction:
    """B. Fact extraction."""

    def test_deposit_facts_extracted(self):
        result = understand_with_mock(
            "My landlord kept my ₹50,000 deposit after I moved out."
        )
        assert "₹50,000" in result.amounts
        roles = [party.role for party in result.parties]
        assert "landlord" in roles
        assert result.primary_issue == "security deposit dispute"
        assert result.jurisdiction is None


class TestJurisdictionHandling:
    """C/D. Unknown vs explicit jurisdiction."""

    def test_unknown_jurisdiction_stays_unknown(self):
        result = understand_with_mock(
            "My employer hasn't paid me for two months."
        )
        assert result.jurisdiction is None

    def test_explicit_jurisdiction_extracted(self):
        result = understand_with_mock(
            "Under Indian law, my employer hasn't paid me for two months."
        )
        assert result.jurisdiction is not None
        assert "India" in result.jurisdiction


class TestNoFabricatedFacts:
    """E. No fabricated facts."""

    def test_minimal_statement_extracts_nothing_invented(self):
        result = understand_with_mock("My landlord kept my deposit.")
        assert result.amounts == []
        assert result.jurisdiction is None
        assert result.dates == []
        assert "unlawful" not in " ".join(result.facts).lower()
        assert "violated" not in " ".join(result.facts).lower()


class TestMissingInformationAndQuestions:
    """F/G. Missing information and clarification-question limit."""

    def test_missing_information_identified(self):
        result = understand_with_mock("My landlord kept my deposit.")
        assert len(result.missing_information) > 0
        assert "jurisdiction" in result.missing_information

    def test_clarification_question_limit(self):
        result = understand_with_mock(
            "My landlord is refusing to return my deposit after I moved out. "
            "What can I do?"
        )
        assert len(result.clarification_questions) <= 5

    def test_model_rejects_too_many_questions(self):
        with pytest.raises(ValidationError):
            LegalQueryUnderstanding(
                intent="general_information",
                legal_domain="unknown",
                clarification_questions=[f"q{i}" for i in range(6)],
            )


class TestConfidenceAndVocabulary:
    """H/I. Confidence bounds and controlled values."""

    def test_confidence_within_bounds(self):
        result = understand_with_mock("How does a lease generally work?")
        assert 0.0 <= result.confidence <= 1.0

    def test_intent_and_domain_within_vocabularies(self):
        result = understand_with_mock("My landlord kept my deposit.")
        assert result.intent in get_args(LegalIntent)
        assert result.legal_domain in get_args(LegalDomain)
        assert result.urgency in ("normal", "time_sensitive", "urgent", "unknown")


class TestSafetyIntegration:
    """J. Query understanding does not bypass existing safety guardrails."""

    def test_escalation_bypasses_provider(self):
        provider = MockDeterministicAIProvider(fixed_reply="Should not be used")
        service = QueryUnderstandingService(provider=provider)
        calls: list = []
        original_generate = provider.generate

        def spy_generate(request):
            calls.append(request)
            return original_generate(request)

        provider.generate = spy_generate  # type: ignore[method-assign]
        result = service.understand("I have court tomorrow!")

        assert calls == []
        assert result.urgency == "urgent"
        # Existing guardrails remain authoritative for the same message.
        assert assess_request("I have court tomorrow!").status == SafetyStatus.ESCALATE


class TestProviderSchemaSelection:
    """K. Gemini provider supports both structured schemas."""

    def test_gemini_produces_query_understanding(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "intent": "dispute_resolution",
                "legal_domain": "landlord_tenant",
                "primary_issue": "security deposit dispute",
                "secondary_issues": [],
                "jurisdiction": None,
                "parties": [{"role": "tenant", "name": None}],
                "facts": ["User states that the deposit was kept."],
                "dates": [],
                "amounts": [],
                "missing_information": ["jurisdiction"],
                "clarification_questions": ["Which state does this concern?"],
                "urgency": "normal",
                "confidence": 0.8,
            }
        )
        mock_client.models.generate_content.return_value = mock_response

        provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        service = QueryUnderstandingService(provider=provider)
        result = service.understand("My landlord kept my deposit.")

        assert isinstance(result, LegalQueryUnderstanding)
        assert result.legal_domain == "landlord_tenant"
        assert result.jurisdiction is None
        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert (
            call_kwargs["config"].response_schema.__name__
            == "LegalQueryUnderstanding"
        )

    def test_unknown_schema_name_rejected(self):
        from app.ai.models.responses import AIRequest

        provider = GeminiAIProvider(
            api_key="test-key", client=MagicMock()
        )
        request = AIRequest(
            system_instruction="Prompt",
            user_message="Query",
            response_schema_name="nonexistent_schema",
        )
        with pytest.raises(GeminiConfigurationError, match="Unsupported"):
            provider.generate(request)

    def test_malformed_understanding_raises_controlled_error(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "NOT VALID JSON"
        mock_client.models.generate_content.return_value = mock_response

        provider = GeminiAIProvider(api_key="test-key", client=mock_client)
        service = QueryUnderstandingService(provider=provider)
        with pytest.raises(GeminiResponseError):
            service.understand("My landlord kept my deposit.")


class TestNoCitations:
    """M. Query understanding fabricates no legal references."""

    def test_schema_has_no_reference_fields(self):
        assert "references" not in LegalQueryUnderstanding.model_fields
        assert "citation" not in LegalQueryUnderstanding.model_fields

    def test_mock_output_contains_no_citations(self):
        provider = MockDeterministicAIProvider()
        from app.ai.models.responses import AIRequest

        response = provider.generate(
            AIRequest(
                system_instruction="Prompt",
                user_message="My landlord kept my deposit.",
                response_schema_name="query_understanding",
            )
        )
        assert "references" not in response.content
        assert "citation" not in response.content.lower()


class TestOrchestratorIntegration:
    """Understanding integrated into the final-answer flow (mock mode)."""

    def test_orchestrator_still_answers_with_mock(self):
        orchestrator = AssistantOrchestrator(
            provider=MockDeterministicAIProvider(fixed_reply="An NDA protects trade secrets.")
        )
        result = orchestrator.process_query("What is an NDA?")
        assert result.answer == "An NDA protects trade secrets."
        assert result.disclaimer != ""
        assert result.references == []

    def test_prompt_version_constant(self):
        assert LEGAL_QUERY_UNDERSTANDING_PROMPT_VERSION == "v1"
