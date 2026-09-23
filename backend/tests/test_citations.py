"""STEP 20 grounded-answer & citation-validation tests.

Deterministic, offline, hermetic: no real Gemini, no network, no external
legal sources. The validator is exercised directly (unit) and through the
assistant orchestrator with a scripted mock provider (integration).
"""

import json
import socket

import pytest
from sqlalchemy.orm import Session

from app.ai.models.responses import (
    AIRequest,
    AIResponse,
    LegalAssistantResponse,
    LegalReferenceItem,
    SafetyStatus,
)
from app.ai.models.retrieval import (
    GroundedContext,
    RetrievedLegalSource,
    RetrievedSourceProvenance,
)
from app.ai.prompts.legal_assistant import (
    LEGAL_ASSISTANT_PROMPT_VERSION,
    LEGAL_ASSISTANT_SYSTEM_PROMPT,
)
from app.ai.providers.base import MockDeterministicAIProvider
from app.ai.safety.guardrails import CENTRAL_LEGAL_DISCLAIMER, assess_request
from app.ai.services.assistant_orchestrator import AssistantOrchestrator
from app.ai.services.citation_validator import (
    ALL_PROTOTYPE_NOTICE,
    build_allowlist,
    validate_references,
    validate_response_citations,
)
from app.services import research_service


def _make_source(
    source_id: str,
    citation_label: str = "Prototype Record",
    title: str | None = None,
    source_type: str = "case",
    jurisdiction: str | None = "Prototype / General",
    prototype: bool = True,
) -> RetrievedLegalSource:
    return RetrievedLegalSource(
        source_id=source_id,
        title=title or f"Title for {source_id}",
        source_type=source_type,
        jurisdiction=jurisdiction,
        date="Sep 20, 2026",
        citation_label=citation_label,
        summary=f"Summary for {source_id}.",
        topics=["topic-a"],
        relevance_score=5.0,
        provenance=RetrievedSourceProvenance(
            source_record_id=source_id,
            source_kind=source_type,
            source_url=None,
            citation_label=citation_label,
            prototype=prototype,
        ),
        prototype=prototype,
    )


def _grounded(*sources: RetrievedLegalSource) -> GroundedContext:
    return GroundedContext(
        query="test query",
        sources=list(sources),
        context_text="ctx",
        source_count=len(sources),
    )


def _empty_grounded() -> GroundedContext:
    return GroundedContext(query="zzzqqq qwxplxkv", sources=[], context_text="",
                           source_count=0)


def _candidate(**overrides) -> LegalReferenceItem:
    base = {"title": "Model Title", "kind": "Case", "citation": "",
            "relevance_note": ""}
    base.update(overrides)
    return LegalReferenceItem(**base)


def _response(*refs: LegalReferenceItem, answer: str = "General answer.") -> LegalAssistantResponse:
    return LegalAssistantResponse(
        answer=answer,
        issue_summary="summary",
        assumptions=[],
        missing_information=[],
        potential_considerations=[],
        suggested_next_steps=[],
        references=list(refs),
        disclaimer=CENTRAL_LEGAL_DISCLAIMER,
        prompt_version=LEGAL_ASSISTANT_PROMPT_VERSION,
        provider_used="deterministic-mock",
    )


class _RecordingProvider(MockDeterministicAIProvider):
    """Mock provider returning scripted final-answer JSON, recording requests."""

    def __init__(self, final_payload) -> None:
        super().__init__()
        self.final_payload = final_payload
        self.seen: list[AIRequest] = []

    def generate(self, request: AIRequest) -> AIResponse:
        self.seen.append(request)
        if request.response_schema_name == "query_understanding":
            return super().generate(request)
        content = (self.final_payload if isinstance(self.final_payload, str)
                   else json.dumps(self.final_payload))
        return AIResponse(content=content, provider=self.provider_name,
                          model="mock-v1", safety_status=SafetyStatus.SAFE)


# --- 1/12. No retrieved sources -> references == [] ------------------------

def test_no_sources_yields_empty_references() -> None:
    result = validate_response_citations(
        _response(_candidate(source_id="research-001",
                             citation="Prototype Record")),
        _empty_grounded(),
    )
    assert result.response.references == []
    assert result.kept_count == 0
    assert result.removed_count == 1
    assert result.allowed_source_ids == []


def test_none_grounded_yields_empty_references() -> None:
    result = validate_response_citations(
        _response(_candidate(source_id="research-001")), None
    )
    assert result.response.references == []
    assert result.removed_count == 1


# --- 2. One valid source -> valid reference preserved & rebuilt -------------

def test_valid_source_id_preserved_with_backend_metadata() -> None:
    grounded = _grounded(_make_source("source-a", citation_label="Prototype Record A"))
    candidate = _candidate(source_id="source-a", citation="Prototype Record A",
                           title="Model-Invented Title", kind="Statute")
    result = validate_response_citations(_response(candidate), grounded)
    assert result.kept_count == 1
    assert result.removed_count == 0
    ref = result.response.references[0]
    assert ref.source_id == "source-a"
    assert ref.title == "Title for source-a"  # backend wins
    assert ref.kind == "case"  # backend controlled vocabulary wins
    assert ref.citation == "Prototype Record A"
    assert result.allowed_source_ids == ["source-a"]


def test_citation_only_match_binds_to_source() -> None:
    grounded = _grounded(_make_source("source-a", citation_label="Prototype Record A"))
    candidate = _candidate(citation="Prototype Record A")
    validated, removed = validate_references([candidate], grounded)
    assert removed == 0
    assert len(validated) == 1
    assert validated[0].source_id == "source-a"


# --- 3/4. Unknown source_id / citation_label rejected -----------------------

def test_unknown_source_id_rejected() -> None:
    grounded = _grounded(_make_source("source-a"))
    validated, removed = validate_references(
        [_candidate(source_id="research-999")], grounded
    )
    assert validated == []
    assert removed == 1


def test_unknown_citation_label_rejected() -> None:
    grounded = _grounded(_make_source("source-a", citation_label="Prototype Record A"))
    validated, removed = validate_references(
        [_candidate(citation="Section 14 of the Rent Control Act")], grounded
    )
    assert validated == []
    assert removed == 1


def test_valid_id_with_foreign_citation_rejected() -> None:
    grounded = _grounded(_make_source("source-a", citation_label="Prototype Record A"))
    validated, removed = validate_references(
        [_candidate(source_id="source-a",
                    citation="Section 14 of the Rent Control Act")],
        grounded,
    )
    assert validated == []
    assert removed == 1


def test_untitled_unbound_reference_rejected() -> None:
    grounded = _grounded(_make_source("source-a"))
    validated, removed = validate_references([_candidate()], grounded)
    assert validated == []
    assert removed == 1


# --- 5. Mixed valid/invalid --------------------------------------------------

def test_mixed_valid_invalid_keeps_only_valid() -> None:
    grounded = _grounded(
        _make_source("source-a", citation_label="Prototype Record A"),
        _make_source("source-c", citation_label="Prototype Record C"),
    )
    candidates = [
        _candidate(source_id="source-a", citation="Prototype Record A"),
        _candidate(source_id="source-b"),
        _candidate(source_id="source-c", citation="Prototype Record C"),
    ]
    validated, removed = validate_references(candidates, grounded)
    assert [r.source_id for r in validated] == ["source-a", "source-c"]
    assert removed == 1


# --- 6. Duplicates deduplicated ----------------------------------------------

def test_duplicate_references_deduplicated() -> None:
    grounded = _grounded(_make_source("source-a"))
    candidates = [_candidate(source_id="source-a"),
                  _candidate(source_id="source-a")]
    validated, removed = validate_references(candidates, grounded)
    assert [r.source_id for r in validated] == ["source-a"]
    assert removed == 0  # collapsed, not counted as fabrication


def test_reference_ordering_deterministic() -> None:
    grounded = _grounded(
        _make_source("source-a"), _make_source("source-b"),
        _make_source("source-c"),
    )
    candidates = [_candidate(source_id="source-c"),
                  _candidate(source_id="source-a"),
                  _candidate(source_id="source-b")]
    first, _ = validate_references(candidates, grounded)
    second, _ = validate_references(list(candidates), grounded)
    assert [r.source_id for r in first] == ["source-c", "source-a", "source-b"]
    assert [r.source_id for r in second] == [r.source_id for r in first]


# --- 7/9. Backend metadata authority + prototype flags ------------------------

def test_backend_metadata_overrides_model() -> None:
    grounded = _grounded(_make_source(
        "source-a", citation_label="Prototype Record A", title="Canonical Title",
        source_type="statute", jurisdiction="Demo Jurisdiction", prototype=True,
    ))
    candidate = _candidate(source_id="source-a", citation="Prototype Record A",
                           title="Fabricated v. Authority", kind="Supreme Court Case")
    # Model even claims non-prototype; backend must win.
    candidate.prototype = False
    validated, _ = validate_references([candidate], grounded)
    ref = validated[0]
    assert ref.title == "Canonical Title"
    assert ref.kind == "statute"
    assert ref.jurisdiction == "Demo Jurisdiction"
    assert ref.prototype is True


def test_prototype_false_preserved_for_verified_source() -> None:
    grounded = _grounded(_make_source("source-v", prototype=False))
    validated, _ = validate_references([_candidate(source_id="source-v")], grounded)
    assert validated[0].prototype is False


def test_prototype_true_preserved() -> None:
    grounded = _grounded(_make_source("source-a", prototype=True))
    validated, _ = validate_references([_candidate(source_id="source-a")], grounded)
    assert validated[0].prototype is True


def test_input_response_not_mutated() -> None:
    grounded = _grounded(_make_source("source-a"))
    original = _response(_candidate(source_id="source-b"))
    validate_response_citations(original, grounded)
    assert len(original.references) == 1  # caller-owned object untouched


# --- 10/13/14. URL, jurisdiction, citation handling ----------------------------

def test_no_source_url_invented_and_note_sanitized() -> None:
    grounded = _grounded(_make_source("source-a"))
    candidate = _candidate(
        source_id="source-a",
        relevance_note="See https://example.com/fake-case for details",
    )
    validated, _ = validate_references([candidate], grounded)
    blob = json.dumps([r.model_dump() for r in validated])
    assert "https://example.com/fake-case" not in blob
    assert "http" not in validated[0].citation
    assert "http" not in validated[0].title


def test_url_citation_rejected() -> None:
    grounded = _grounded(_make_source("source-a", citation_label="Prototype Record A"))
    validated, removed = validate_references(
        [_candidate(citation="https://courts.example.gov/fake")], grounded
    )
    assert validated == []
    assert removed == 1


def test_null_jurisdiction_remains_null() -> None:
    grounded = _grounded(_make_source("source-a", jurisdiction=None))
    validated, _ = validate_references([_candidate(source_id="source-a")], grounded)
    assert validated[0].jurisdiction is None


def test_existing_citation_label_retained() -> None:
    grounded = _grounded(_make_source("source-a", citation_label="Demo case record"))
    validated, _ = validate_references([_candidate(source_id="source-a")], grounded)
    assert validated[0].citation == "Demo case record"


# --- 11. Unlisted sources can never be introduced ------------------------------

def test_gemini_cannot_introduce_unlisted_source() -> None:
    grounded = _grounded(_make_source("source-a"))
    invented = _candidate(source_id="Sharma v. State (2024) 5 SCC 123",
                          citation="Sharma v. State (2024) 5 SCC 123",
                          title="Sharma v. State", kind="Supreme Court Case")
    validated, removed = validate_references([invented], grounded)
    assert validated == []
    assert removed == 1


# --- 16/17. No provider, no network --------------------------------------------

def test_validation_is_pure_no_provider_or_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted during validation")

    monkeypatch.setattr(socket, "create_connection", _boom)
    monkeypatch.setattr(socket, "getaddrinfo", _boom)
    grounded = _grounded(_make_source("source-a"))
    result = validate_response_citations(
        _response(_candidate(source_id="source-a")), grounded
    )
    assert result.kept_count == 1
    assert result.response.references[0].source_id == "source-a"


# --- Prompt contract ------------------------------------------------------------

def test_grounding_prompt_rules_present() -> None:
    assert "SOURCE GROUNDING & CITATIONS" in LEGAL_ASSISTANT_SYSTEM_PROMPT
    assert "ONLY permitted basis for source-based claims" in LEGAL_ASSISTANT_SYSTEM_PROMPT
    assert "Treat prototype records as informational research material" in LEGAL_ASSISTANT_SYSTEM_PROMPT
    assert "not verified legal authority" in LEGAL_ASSISTANT_SYSTEM_PROMPT
    assert "Do not infer jurisdiction" in LEGAL_ASSISTANT_SYSTEM_PROMPT
    # Existing contract untouched.
    assert LEGAL_ASSISTANT_PROMPT_VERSION == "v1"
    assert "LEGAL INFORMATION, NOT LEGAL ADVICE" in LEGAL_ASSISTANT_SYSTEM_PROMPT


# --- 18. ESCALATE still short-circuits before retrieval --------------------------

def test_escalate_short_circuits_before_retrieval_and_validation() -> None:
    calls: list = []
    provider = _RecordingProvider({"answer": "never"})
    orchestrator = AssistantOrchestrator(provider=provider)

    def _resolver(query, understanding):
        calls.append(query)
        raise AssertionError("retrieval must not run on ESCALATE")

    result = orchestrator.process_query("I have court tomorrow!", retrieval_resolver=_resolver)
    assert result.safety_assessment.status == SafetyStatus.ESCALATE
    assert result.references == []
    assert calls == []
    assert assess_request("I have court tomorrow!").status == SafetyStatus.ESCALATE


# --- 20/22/23. Orchestrator integration -------------------------------------------

def test_orchestrator_empty_retrieval_strips_fabricated_refs() -> None:
    final = {
        "answer": "Answer text.",
        "references": [{"title": "Fabricated Case v. Authority",
                        "kind": "Case", "source_id": "research-999",
                        "citation": "Fake Citation"}],
    }
    provider = _RecordingProvider(final)
    orchestrator = AssistantOrchestrator(provider=provider)
    result = orchestrator.process_query(
        "Tell me a case about deposits",
        retrieval_resolver=lambda q, u: _empty_grounded(),
    )
    assert result.references == []


def test_orchestrator_valid_and_invalid_refs_filtered(db: Session) -> None:
    grounded = research_service.retrieve_grounded(db, "security deposit dispute")
    assert grounded.source_count >= 1
    real_id = grounded.sources[0].source_id
    real_citation = grounded.sources[0].citation_label
    final = {
        "answer": "Deposit information grounded in the retrieved record.",
        "references": [
            {"title": "Wrong Title", "kind": "Wrong Kind",
             "source_id": real_id, "citation": real_citation,
             "relevance_note": "Lease deposit note."},
            {"title": "Fabricated", "kind": "Case", "source_id": "ghost-id",
             "citation": "Ghost Citation"},
        ],
    }
    provider = _RecordingProvider(final)
    orchestrator = AssistantOrchestrator(provider=provider)
    result = orchestrator.process_query(
        "My landlord kept my security deposit after I moved out.",
        retrieval_resolver=lambda q, u: grounded,
    )
    assert len(result.references) == 1
    ref = result.references[0]
    assert ref.source_id == real_id
    assert ref.title == grounded.sources[0].title
    assert ref.citation == real_citation
    assert ref.prototype is True
    # All seed records are prototype: the limitation must be communicated once.
    assert ALL_PROTOTYPE_NOTICE in result.answer
    assert result.answer.count(ALL_PROTOTYPE_NOTICE) == 1


def test_orchestrator_end_to_end_mocked_grounded_flow(db: Session) -> None:
    """user query -> understanding -> retrieval -> grounded context ->
    mocked final response -> citation validation -> final response."""
    grounded = research_service.retrieve_grounded(db, "security deposit dispute")
    real_id = grounded.sources[0].source_id
    real_citation = grounded.sources[0].citation_label
    final = {
        "answer": "General deposit guidance with a grounded reference.",
        "issue_summary": "Security deposit inquiry",
        "assumptions": [],
        "missing_information": ["Applicable jurisdiction"],
        "potential_considerations": ["Deposit return timelines vary."],
        "suggested_next_steps": ["Review the tenancy agreement."],
        "references": [{"title": real_id, "kind": "case",
                        "source_id": real_id, "citation": real_citation,
                        "relevance_note": "Directly on point."}],
    }
    provider = _RecordingProvider(final)
    orchestrator = AssistantOrchestrator(provider=provider)
    result = orchestrator.process_query(
        "My landlord kept my security deposit after I moved out.",
        retrieval_resolver=lambda q, u: grounded,
    )
    assert result.references[0].source_id == real_id
    assert result.disclaimer == CENTRAL_LEGAL_DISCLAIMER
    assert result.safety_assessment.status == SafetyStatus.SAFE
    # Grounded chunks actually reached the final-answer request.
    final_requests = [r for r in provider.seen
                      if r.response_schema_name == "legal_assistant"]
    assert final_requests[0].retrieved_context == [grounded.context_text]


# --- Security (23) -----------------------------------------------------------------

def test_api_key_material_cannot_become_reference() -> None:
    grounded = _grounded(_make_source("source-a", citation_label="Prototype Record A"))
    secret = "AIzaSySecretApiKey123456789"
    candidates = [
        _candidate(source_id="source-a", citation=secret),
        _candidate(source_id=secret, citation="Prototype Record A"),
        _candidate(source_id="source-a", title=secret,
                   citation="Prototype Record A"),
    ]
    validated, removed = validate_references(candidates[:2], grounded)
    assert validated == []
    assert removed == 2
    # A model-supplied title carrying secret material is discarded: the
    # reference is rebuilt purely from backend metadata.
    rebuilt, _ = validate_references(candidates[2:], grounded)
    assert len(rebuilt) == 1
    assert secret not in json.dumps(rebuilt[0].model_dump())


def test_provider_error_text_cannot_become_citation() -> None:
    grounded = _grounded(_make_source("source-a", citation_label="Prototype Record A"))
    candidate = _candidate(citation="GeminiResponseError: quota exceeded (retry)")
    validated, removed = validate_references([candidate], grounded)
    assert validated == []
    assert removed == 1


def test_prototype_record_cannot_be_promoted() -> None:
    grounded = _grounded(_make_source("source-a", prototype=True))
    candidate = _candidate(source_id="source-a")
    candidate.prototype = False  # model claims verified status
    result = validate_response_citations(_response(candidate), grounded)
    assert result.response.references[0].prototype is True
    assert ALL_PROTOTYPE_NOTICE in result.response.answer


def test_allowlist_built_dynamically_from_context() -> None:
    first = _grounded(_make_source("alpha"), _make_source("beta"))
    second = _grounded(_make_source("gamma"))
    assert sorted(build_allowlist(first)) == ["alpha", "beta"]
    assert sorted(build_allowlist(second)) == ["gamma"]
    assert build_allowlist(None) == {}
    assert build_allowlist(_empty_grounded()) == {}
