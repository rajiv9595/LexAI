"""STEP 21: Assistant API exposes STEP 20 validated references.

All provider behavior is faked (deterministic mock / stubbed orchestrators);
no test reaches the real Gemini API and no external calls are made.
"""

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from app.ai.models.responses import AIRequest, AIResponse, SafetyStatus
from app.ai.providers.base import MockDeterministicAIProvider
from app.ai.services.assistant_orchestrator import AssistantOrchestrator
from app.schemas.assistant import ValidatedAssistantReference
from app.services import assistant_service


def _enable_ai(monkeypatch: pytest.MonkeyPatch, orchestrator_factory) -> None:
    monkeypatch.setattr(assistant_service.settings, "ai_enabled", True)
    monkeypatch.setattr(
        assistant_service, "AssistantOrchestrator", orchestrator_factory
    )


class _ScriptedMock(MockDeterministicAIProvider):
    """Mock provider returning scripted final-answer JSON (offline)."""

    def __init__(self, final_payload) -> None:
        super().__init__()
        self.final_payload = final_payload

    def generate(self, request: AIRequest) -> AIResponse:
        if request.response_schema_name == "query_understanding":
            return super().generate(request)
        content = (
            self.final_payload
            if isinstance(self.final_payload, str)
            else json.dumps(self.final_payload)
        )
        return AIResponse(
            content=content,
            provider=self.provider_name,
            model="mock-v1",
            safety_status=SafetyStatus.SAFE,
        )


def _real_orchestrator_with(final_payload):
    def _factory(*args, **kwargs):
        return AssistantOrchestrator(provider=_ScriptedMock(final_payload))

    return _factory


class _NoRefsOrchestrator:
    """Legacy/stub shape without a references attribute."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    def process_query(self, **kwargs):
        return SimpleNamespace(answer="AI answer without references")


def test_prototype_reply_returns_empty_references(
    auth_client: TestClient,
) -> None:
    response = auth_client.post(
        "/api/v1/assistant/messages",
        json={"message": "What should I check before signing a contract?"},
    )
    assert response.status_code == 200
    assert response.json()["references"] == []


def test_stub_without_references_attr_returns_empty_list(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_ai(monkeypatch, _NoRefsOrchestrator)
    response = auth_client.post(
        "/api/v1/assistant/messages", json={"message": "Hello"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "AI answer without references"
    assert body["references"] == []


def test_validated_references_serialized(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    final = {
        "answer": "Deposit guidance grounded in the retrieved record.",
        "references": [
            {
                "title": "Model Tampered Title",
                "kind": "Supreme Court Case",
                "source_id": "rental-deposit-dispute",
                "citation": "Demo case record",
                "relevance_note": "On point.",
            },
            {
                "title": "Fabricated v. Authority",
                "kind": "Case",
                "source_id": "ghost-source",
                "citation": "Ghost citation",
            },
        ],
    }
    _enable_ai(monkeypatch, _real_orchestrator_with(final))
    response = auth_client.post(
        "/api/v1/assistant/messages",
        json={"message": "My landlord kept my security deposit after I moved out."},
    )
    assert response.status_code == 200
    refs = response.json()["references"]
    # Fake source removed by STEP 20 validation; never reaches the API.
    assert [r["source_id"] for r in refs] == ["rental-deposit-dispute"]
    ref = refs[0]
    # Backend metadata is authoritative, not model output.
    assert ref["title"] == "Rental Deposit Dispute — Prototype Research Record"
    assert ref["citation_label"] == "Demo case record"
    assert ref["source_type"] == "case"
    assert ref["prototype"] is True
    assert ref["jurisdiction"] == "Prototype / General"
    # No internal-only fields leak.
    assert set(ref.keys()) == {
        "source_id",
        "title",
        "citation_label",
        "source_type",
        "jurisdiction",
        "prototype",
    }


def test_tampered_prototype_flag_not_propagated(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    final = {
        "answer": "Answer.",
        "references": [
            {
                "title": "x",
                "kind": "case",
                "source_id": "rental-deposit-dispute",
                "citation": "Demo case record",
                "prototype": False,
            }
        ],
    }
    _enable_ai(monkeypatch, _real_orchestrator_with(final))
    response = auth_client.post(
        "/api/v1/assistant/messages",
        json={"message": "My landlord kept my security deposit."},
    )
    assert response.json()["references"][0]["prototype"] is True


def test_empty_retrieval_yields_empty_references(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    final = {
        "answer": "General guidance.",
        "references": [
            {
                "title": "Fabricated",
                "kind": "Case",
                "source_id": "invented-id",
                "citation": "Invented citation",
            }
        ],
    }
    _enable_ai(monkeypatch, _real_orchestrator_with(final))
    response = auth_client.post(
        "/api/v1/assistant/messages", json={"message": "zzzqqq qwxplxkv"}
    )
    assert response.status_code == 200
    assert response.json()["references"] == []


def test_escalate_response_has_empty_references(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(assistant_service.settings, "ai_enabled", True)
    response = auth_client.post(
        "/api/v1/assistant/messages", json={"message": "I have court tomorrow!"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["references"] == []
    assert "URGENT" in body["content"]


def test_validated_reference_dto_shape() -> None:
    ref = ValidatedAssistantReference(
        source_id="rental-deposit-dispute",
        title="Rental Deposit Dispute — Prototype Research Record",
        citation_label="Demo case record",
        source_type="case",
        jurisdiction="Prototype / General",
        prototype=True,
    )
    dumped = ref.model_dump()
    assert "source_url" not in dumped
    assert "relevance_note" not in dumped
    assert "api_key" not in json.dumps(dumped).lower()
