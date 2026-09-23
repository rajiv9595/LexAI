"""STEP 19 retrieval-foundation tests: deterministic, offline, no external calls."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.models.query_understanding import LegalQueryUnderstanding
from app.ai.models.responses import AIRequest, AIResponse, SafetyStatus
from app.ai.models.retrieval import GroundedContext
from app.ai.providers.base import AIProvider, MockDeterministicAIProvider
from app.ai.safety.guardrails import assess_request
from app.ai.services import research_retriever
from app.ai.services.assistant_orchestrator import AssistantOrchestrator
from app.ai.services.research_retriever import (
    build_retrieval_terms,
    format_grounded_context,
    grounded_context_to_chunks,
    retrieve,
)
from app.repositories import research_repository
from app.services import research_service


def _understanding(**overrides) -> LegalQueryUnderstanding:
    base = {
        "intent": "general_information",
        "legal_domain": "unknown",
        "primary_issue": None,
        "secondary_issues": [],
        "jurisdiction": None,
        "urgency": "normal",
        "confidence": 0.8,
    }
    base.update(overrides)
    return LegalQueryUnderstanding(**base)


def _seeded_records(db: Session):
    return research_repository.list_all(db)


# 1. Exact title match ranks highly.
def test_exact_title_match_ranks_highly(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "Rental Deposit Dispute")
    assert ctx.source_count >= 1
    assert ctx.sources[0].source_id == "rental-deposit-dispute"


# 2. Topic match ranks appropriately.
def test_topic_match_ranks_appropriately(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "Workplace rights")
    ids = [s.source_id for s in ctx.sources]
    assert "employment-termination" in ids


# 3. Summary match works.
def test_summary_match_works(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "confidentiality duties")
    assert any(s.source_id == "confidentiality-obligations" for s in ctx.sources)


# 4. Multiple keyword matches increase relevance.
def test_multiple_keywords_increase_relevance(db: Session) -> None:
    records = _seeded_records(db)
    single = retrieve(records, "deposit")
    multi = retrieve(records, "rental deposit dispute security tenant")
    single_score = next(
        s.relevance_score for s in single.sources if s.source_id == "rental-deposit-dispute"
    )
    multi_score = next(
        s.relevance_score for s in multi.sources if s.source_id == "rental-deposit-dispute"
    )
    assert multi_score > single_score


# 5. Results are sorted deterministically.
def test_results_sorted_deterministically(db: Session) -> None:
    records = _seeded_records(db)
    first = retrieve(records, "demonstration record")
    second = retrieve(records, "demonstration record")
    assert [s.source_id for s in first.sources] == [s.source_id for s in second.sources]
    scores = [s.relevance_score for s in first.sources]
    assert scores == sorted(scores, reverse=True)


# 6. Limit is respected.
def test_limit_is_respected(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "demonstration record", limit=2)
    assert ctx.source_count == 2
    assert len(ctx.sources) == 2


# 7. Empty query handled safely.
def test_empty_query_handled_safely(db: Session) -> None:
    records = _seeded_records(db)
    for query in ("", "   ", "the and of"):
        ctx = retrieve(records, query)
        assert ctx.sources == []
        assert ctx.source_count == 0
        assert ctx.context_text == ""


# 8. No-result query returns empty grounded context.
def test_no_result_query_returns_empty(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "zzzqqq qwxplxkv")
    assert ctx.sources == []
    assert ctx.source_count == 0
    assert ctx.context_text == ""


# 9. Existing source_type values are preserved.
def test_source_type_values_preserved(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "deposit")
    rental = next(s for s in ctx.sources if s.source_id == "rental-deposit-dispute")
    assert rental.source_type == "case"
    assert rental.provenance.source_kind == "case"


# 10. Existing jurisdiction is preserved.
def test_jurisdiction_preserved(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "deposit")
    rental = next(s for s in ctx.sources if s.source_id == "rental-deposit-dispute")
    assert rental.jurisdiction == "Prototype / General"


# 11. Null jurisdiction remains null.
def test_null_jurisdiction_remains_null() -> None:
    record = {
        "id": "null-jur",
        "title": "Deposit helpers",
        "source_type": "case",
        "jurisdiction": None,
        "date": "Sep 20, 2026",
        "citation_label": "Demo",
        "summary": "deposit summary",
        "topics": ["deposit"],
        "prototype": True,
    }
    ctx = retrieve([record], "deposit")
    assert ctx.sources[0].jurisdiction is None


# 12. Prototype flag is preserved.
def test_prototype_flag_preserved(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "deposit")
    assert all(s.prototype is True for s in ctx.sources)
    assert all(s.provenance.prototype is True for s in ctx.sources)


# 13. Existing citation_label is preserved.
def test_citation_label_preserved(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "deposit")
    rental = next(s for s in ctx.sources if s.source_id == "rental-deposit-dispute")
    assert rental.citation_label == "Demo case record"
    assert rental.provenance.citation_label == "Demo case record"


# 14. Missing source URL remains null rather than fabricated.
def test_missing_source_url_remains_null(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "deposit")
    assert all(s.provenance.source_url is None for s in ctx.sources)


# 15. No citation is invented (empty retrieval invents nothing; URLs absent).
def test_no_citation_invented(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "zzzqqq qwxplxkv")
    assert ctx.sources == []
    assert "http" not in ctx.context_text
    seeded = retrieve(records, "deposit")
    assert "http" not in seeded.context_text.lower()
    assert "india.gov.in" not in seeded.context_text.lower()


# 16. No legal conclusion is generated by the retriever.
def test_no_legal_conclusion_generated(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "My landlord kept my security deposit after I moved out.")
    blob = " ".join([ctx.context_text] + [s.summary for s in ctx.sources]).lower()
    assert "violated" not in blob
    assert "unlawful" not in blob
    assert "indian rental law" not in blob


# 17. User-stated facts are not converted into legal findings.
def test_facts_not_converted_into_findings() -> None:
    # The raw query is searched verbatim, but the retriever must never
    # rewrite user statements into legal conclusions (e.g. "violated",
    # "unlawful") or invent a jurisdiction.
    terms = build_retrieval_terms(
        "My landlord Rajiv kept my deposit of Rs 50000",
        _understanding(primary_issue="security deposit dispute"),
    )
    joined = " ".join(terms)
    assert "deposit" in joined
    assert "security" in joined
    assert "dispute" in joined
    for conclusion in ("violated", "unlawful", "guilty", "liable", "india"):
        assert conclusion not in joined


# 18. Query understanding jurisdiction is not inferred.
def test_jurisdiction_not_inferred() -> None:
    understanding = _understanding(jurisdiction=None)
    terms = build_retrieval_terms("My landlord kept my deposit", understanding)
    assert not any(t in ("india", "texas") for t in terms)
    record = {
        "id": "rec-a",
        "title": "deposit record",
        "source_type": "case",
        "jurisdiction": "India",
        "date": "Sep 20, 2026",
        "citation_label": "Demo",
        "summary": "deposit summary",
        "topics": ["deposit"],
        "prototype": True,
    }
    without = retrieve([record], "deposit", understanding)
    with_jur = retrieve(
        [record], "deposit", _understanding(jurisdiction="India")
    )
    assert with_jur.sources[0].relevance_score > without.sources[0].relevance_score


# 19. Retrieval can consume LegalQueryUnderstanding.
def test_retrieval_consumes_understanding(db: Session) -> None:
    records = _seeded_records(db)
    understanding = _understanding(
        legal_domain="landlord_tenant",
        primary_issue="security deposit dispute",
        secondary_issues=["tenant rights"],
    )
    ctx = retrieve(records, "deposit question", understanding)
    assert ctx.sources[0].source_id == "rental-deposit-dispute"


# 20. Retrieval works with understanding jurisdiction = null.
def test_retrieval_with_null_jurisdiction(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "deposit", _understanding(jurisdiction=None))
    assert ctx.source_count >= 1


# 21. Retrieved context formatting is deterministic.
def test_context_formatting_deterministic(db: Session) -> None:
    records = _seeded_records(db)
    first = retrieve(records, "deposit")
    second = retrieve(records, "deposit")
    assert first.context_text == second.context_text
    assert format_grounded_context(first.sources) == first.context_text
    assert "SOURCE 1" in first.context_text
    assert "Prototype: true" in first.context_text


# 22. Source IDs are stable.
def test_source_ids_stable(db: Session) -> None:
    records = _seeded_records(db)
    ctx = retrieve(records, "deposit")
    for source in ctx.sources:
        assert source.source_id == source.provenance.source_record_id


# 23. AIRequest.retrieved_context receives the retrieved material correctly.
class _CapturingMock(MockDeterministicAIProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen: list[AIRequest] = []

    def generate(self, request: AIRequest) -> AIResponse:
        self.seen.append(request)
        return super().generate(request)


def test_orchestrator_passes_grounded_context_to_airequest(db: Session) -> None:
    records = _seeded_records(db)
    expected = retrieve(records, "security deposit", _understanding())
    provider = _CapturingMock()
    orchestrator = AssistantOrchestrator(provider=provider)

    def _resolver(query: str, understanding) -> GroundedContext:
        return expected

    result = orchestrator.process_query(
        "What about my security deposit?", retrieval_resolver=_resolver
    )
    assert result.answer  # pipeline completed
    final_requests = [
        r for r in provider.seen if r.response_schema_name == "legal_assistant"
    ]
    assert len(final_requests) == 1
    assert final_requests[0].retrieved_context == [expected.context_text]


def test_explicit_retrieved_context_wins_over_resolver() -> None:
    provider = _CapturingMock()
    orchestrator = AssistantOrchestrator(provider=provider)

    def _resolver(query: str, understanding) -> GroundedContext:
        raise AssertionError("resolver must not be called when context is explicit")

    orchestrator.process_query(
        "What is an NDA?",
        retrieved_context=["explicit chunk"],
        retrieval_resolver=_resolver,
    )
    final_requests = [
        r for r in provider.seen if r.response_schema_name == "legal_assistant"
    ]
    assert final_requests[0].retrieved_context == ["explicit chunk"]


# 24. Empty retrieval does not create fake context.
def test_empty_retrieval_creates_no_fake_context() -> None:
    empty = GroundedContext(
        query="zzzqqq", sources=[], context_text="", source_count=0
    )
    assert grounded_context_to_chunks(empty) == []
    assert grounded_context_to_chunks(None) == []

    provider = _CapturingMock()
    orchestrator = AssistantOrchestrator(provider=provider)
    result = orchestrator.process_query(
        "zzzqqq nonexistent topic",
        retrieval_resolver=lambda q, u: empty,
    )
    assert result.references == []
    final_requests = [
        r for r in provider.seen if r.response_schema_name == "legal_assistant"
    ]
    assert final_requests[0].retrieved_context == []


# 25. Existing assistant safety ESCALATE behavior remains unchanged.
def test_escalate_short_circuit_skips_retrieval() -> None:
    calls: list = []
    provider = _CapturingMock(fixed_reply="Should not be called")
    orchestrator = AssistantOrchestrator(provider=provider)

    def _resolver(query: str, understanding):
        calls.append((query, understanding))
        raise AssertionError("retrieval must not run on ESCALATE")

    result = orchestrator.process_query(
        "I have court tomorrow!", retrieval_resolver=_resolver
    )
    assert result.safety_assessment.status == SafetyStatus.ESCALATE
    assert "URGENT:" in result.answer
    assert calls == []
    assert assess_request("I have court tomorrow!").status == SafetyStatus.ESCALATE


# 26/27/28. Existing research API, query-understanding, and mock provider behavior unchanged.
def test_research_api_compat_preserved(client: TestClient) -> None:
    response = client.post(
        "/api/v1/research/search", json={"query": "security deposit dispute"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["prototype"] is True
    assert body["count"] >= 1
    detail = client.get("/api/v1/research/rental-deposit-dispute")
    assert detail.status_code == 200
    assert detail.json()["prototype"] is True


def test_retriever_reads_canonical_records(db: Session, client: TestClient) -> None:
    body = client.post(
        "/api/v1/research/search", json={"query": "deposit"}
    ).json()
    api_ids = {item["result_id"] for item in body["results"]}
    grounded = research_service.retrieve_grounded(db, "deposit")
    grounded_ids = {s.source_id for s in grounded.sources}
    assert grounded_ids <= api_ids
    assert grounded.retrieval_method == "lexical-weighted-v1"


class _PassthroughProvider(AIProvider):
    @property
    def provider_name(self) -> str:
        return "passthrough-test"

    def generate(self, request: AIRequest) -> AIResponse:
        from app.ai.models.responses import SafetyStatus as _SS

        return AIResponse(
            content="ok", provider=self.provider_name, model="t",
            safety_status=_SS.SAFE,
        )
