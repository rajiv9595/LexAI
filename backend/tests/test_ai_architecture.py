"""Unit tests for the provider-independent AI architecture, prompts, safety guardrails, and orchestrator."""

import pytest
from pydantic import ValidationError

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
from app.ai.prompts.legal_assistant import (
    LEGAL_ASSISTANT_PROMPT_VERSION,
    LEGAL_ASSISTANT_SYSTEM_PROMPT,
)
from app.ai.providers.base import AIProvider, MockDeterministicAIProvider
from app.ai.safety.guardrails import (
    CENTRAL_LEGAL_DISCLAIMER,
    assess_request,
    validate_response,
)
from app.ai.services.assistant_orchestrator import AssistantOrchestrator


class TestAIModels:
    """Test AI request, response, and domain models."""

    def test_ai_request_valid(self):
        request = AIRequest(
            system_instruction="You are a legal assistant.",
            user_message="What is an NDA?",
            conversation_history=[
                AIRequestMessage(role="user", content="Hello"),
                AIRequestMessage(role="assistant", content="Hi, how can I help?"),
            ],
            retrieved_context=["An NDA is a Non-Disclosure Agreement."],
            case_context={"user_tier": "standard"},
            temperature=0.3,
            max_tokens=500,
        )
        assert request.user_message == "What is an NDA?"
        assert len(request.conversation_history) == 2
        assert request.temperature == 0.3
        assert request.max_tokens == 500

    def test_ai_request_validation_error_on_empty(self):
        with pytest.raises(ValidationError):
            AIRequest(system_instruction="Prompt", user_message="")

    def test_ai_response_defaults(self):
        response = AIResponse(
            content="This is generated text.",
            provider="test-provider",
            model="test-model",
        )
        assert response.content == "This is generated text."
        assert response.finish_reason == "stop"
        assert response.safety_status == SafetyStatus.SAFE
        assert response.prompt_tokens is None

    def test_legal_assistant_response_contract(self):
        response = LegalAssistantResponse(
            answer="A lease agreement outlines rental conditions.",
            issue_summary="Residential tenancy query",
            assumptions=["Standard residential tenancy"],
            missing_information=["Lease start date"],
            potential_considerations=["Notice period before termination"],
            suggested_next_steps=["Review tenancy clauses"],
            references=[
                LegalReferenceItem(
                    title="Transfer of Property Act",
                    kind="Statute",
                    citation="Section 105",
                    relevance_note="Defines leases of immovable property",
                )
            ],
            disclaimer=CENTRAL_LEGAL_DISCLAIMER,
            safety_assessment=SafetyAssessment(status=SafetyStatus.SAFE),
            prompt_version=LEGAL_ASSISTANT_PROMPT_VERSION,
            provider_used="deterministic-mock",
        )
        assert response.answer.startswith("A lease agreement")
        assert len(response.references) == 1
        assert response.prompt_version == "v1"
        assert response.disclaimer == CENTRAL_LEGAL_DISCLAIMER


class TestAIProviders:
    """Test provider interfaces and deterministic mock implementations."""

    def test_mock_deterministic_provider(self):
        provider = MockDeterministicAIProvider(fixed_reply="Fixed test answer.")
        assert provider.provider_name == "deterministic-mock"

        request = AIRequest(
            system_instruction="System prompt",
            user_message="Tell me about contracts.",
        )
        response = provider.generate(request)
        assert isinstance(response, AIResponse)
        assert response.content == "Fixed test answer."
        assert response.provider == "deterministic-mock"
        assert response.safety_status == SafetyStatus.SAFE
        assert response.prompt_tokens is not None
        assert response.completion_tokens is not None

    def test_provider_interface_subclass(self):
        class CustomProvider(AIProvider):
            @property
            def provider_name(self) -> str:
                return "custom-test"

            def generate(self, request: AIRequest) -> AIResponse:
                return AIResponse(
                    content=f"Custom: {request.user_message}",
                    provider=self.provider_name,
                    model="custom-1",
                )

        custom = CustomProvider()
        req = AIRequest(system_instruction="Sys", user_message="Hello")
        resp = custom.generate(req)
        assert resp.content == "Custom: Hello"
        assert resp.provider == "custom-test"


class TestPromptsAndVersioning:
    """Test prompt versioning and content integrity."""

    def test_prompt_version(self):
        assert LEGAL_ASSISTANT_PROMPT_VERSION == "v1"

    def test_prompt_content_rules(self):
        assert "LEGAL INFORMATION, NOT LEGAL ADVICE" in LEGAL_ASSISTANT_SYSTEM_PROMPT
        assert "TRUTHFULNESS & GROUNDING" in LEGAL_ASSISTANT_SYSTEM_PROMPT
        assert "UNCERTAINTY & MISSING FACTS" in LEGAL_ASSISTANT_SYSTEM_PROMPT
        assert "SAFETY & HIGH-RISK SITUATIONS" in LEGAL_ASSISTANT_SYSTEM_PROMPT
        assert "attorney-client relationship" in LEGAL_ASSISTANT_SYSTEM_PROMPT.lower()


class TestSafetyGuardrails:
    """Test pre- and post-generation safety assessments and guardrails."""

    def test_safe_request_classification(self):
        assessment = assess_request(
            "Can you explain what a rental agreement generally contains?"
        )
        assert assessment.status == SafetyStatus.SAFE
        assert assessment.requires_professional_review is False
        assert len(assessment.flags) == 0

    def test_caution_request_classification(self):
        assessment = assess_request(
            "I received a legal notice from my landlord and don't understand it."
        )
        assert assessment.status == SafetyStatus.CAUTION
        assert assessment.requires_professional_review is True
        assert any(f.flag_name == "active_legal_notice" for f in assessment.flags)
        assert "NOTICE:" in assessment.advisory_message

    def test_escalate_immediate_danger(self):
        assessment = assess_request(
            "I am in immediate danger of domestic abuse."
        )
        assert assessment.status == SafetyStatus.ESCALATE
        assert assessment.requires_professional_review is True
        assert any(f.flag_name == "emergency_physical_safety" for f in assessment.flags)
        assert "URGENT:" in assessment.advisory_message

    def test_escalate_court_deadline(self):
        assessment = assess_request(
            "I have court tomorrow and don't know what to do."
        )
        assert assessment.status == SafetyStatus.ESCALATE
        assert assessment.requires_professional_review is True
        assert any(f.flag_name == "imminent_court_deadline" for f in assessment.flags)

    def test_escalate_criminal_custody(self):
        assessment = assess_request(
            "My brother was arrested and is currently in jail."
        )
        assert assessment.status == SafetyStatus.ESCALATE
        assert any(f.flag_name == "criminal_custody_interrogation" for f in assessment.flags)

    def test_escalate_fraud_law_evasion(self):
        assessment = assess_request(
            "How can I hide assets from the court during a trial?"
        )
        assert assessment.status == SafetyStatus.ESCALATE
        assert any(f.flag_name == "fraud_and_law_evasion" for f in assessment.flags)

    def test_validate_response_clean(self):
        is_valid, violations = validate_response(
            "Standard residential leases typically define the rent and term.",
            SafetyAssessment(status=SafetyStatus.SAFE),
        )
        assert is_valid is True
        assert len(violations) == 0

    def test_validate_response_prohibited_guarantee(self):
        is_valid, violations = validate_response(
            "If you file this motion, I guarantee you will win the case.",
            SafetyAssessment(status=SafetyStatus.SAFE),
        )
        assert is_valid is False
        assert len(violations) > 0

    def test_validate_response_prohibited_representation(self):
        is_valid, violations = validate_response(
            "As your lawyer, I advise you to sign immediately.",
            SafetyAssessment(status=SafetyStatus.SAFE),
        )
        assert is_valid is False
        assert len(violations) > 0

    def test_central_legal_disclaimer(self):
        assert len(CENTRAL_LEGAL_DISCLAIMER) > 50
        assert "attorney-client relationship" in CENTRAL_LEGAL_DISCLAIMER
        assert "not a law firm" in CENTRAL_LEGAL_DISCLAIMER


class TestAssistantOrchestrator:
    """Test full pipeline orchestration and safety integration."""

    def test_orchestrator_safe_pipeline(self):
        orchestrator = AssistantOrchestrator(
            provider=MockDeterministicAIProvider(fixed_reply="An NDA protects trade secrets.")
        )
        result = orchestrator.process_query("What is an NDA?")

        assert isinstance(result, LegalAssistantResponse)
        assert result.answer == "An NDA protects trade secrets."
        assert result.safety_assessment.status == SafetyStatus.SAFE
        assert result.disclaimer == CENTRAL_LEGAL_DISCLAIMER
        assert result.prompt_version == "v1"
        assert result.provider_used == "deterministic-mock"

    def test_orchestrator_escalate_short_circuit(self):
        orchestrator = AssistantOrchestrator(
            provider=MockDeterministicAIProvider(fixed_reply="Should not be called")
        )
        result = orchestrator.process_query("I have court tomorrow!")

        assert result.safety_assessment.status == SafetyStatus.ESCALATE
        assert "URGENT:" in result.answer
        assert result.answer != "Should not be called"
        assert result.disclaimer == CENTRAL_LEGAL_DISCLAIMER

    def test_orchestrator_caution_flow(self):
        orchestrator = AssistantOrchestrator(
            provider=MockDeterministicAIProvider(fixed_reply="Review your summons carefully.")
        )
        result = orchestrator.process_query("I was served with papers today.")

        assert result.safety_assessment.status == SafetyStatus.CAUTION
        assert result.answer == "Review your summons carefully."
        assert result.safety_assessment.requires_professional_review is True

    def test_orchestrator_post_validation_handling(self):
        orchestrator = AssistantOrchestrator(
            provider=MockDeterministicAIProvider(fixed_reply="I guarantee you will win.")
        )
        result = orchestrator.process_query("Will I win?")

        assert "I guarantee you will win." in result.answer
        assert "[Notice: This response provides general legal information" in result.answer
