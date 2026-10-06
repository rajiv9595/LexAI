"""Research application logic over persisted prototype records."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.models.query_understanding import LegalQueryUnderstanding
from app.ai.models.retrieval import GroundedContext
from app.ai.services import research_retriever
from app.models.research import ResearchRecord
from app.models.research_evidence import ResearchEvidence
from app.ai.models.retrieval import RetrievedEvidencePassage
from app.repositories import research_repository
from app.schemas.research import (
    ResearchResultResponse,
    ResearchSearchRequest,
    ResearchSearchResponse,
)


def search_prototype(
    db: Session, payload: ResearchSearchRequest
) -> ResearchSearchResponse:
    """Run a deterministic local search over persisted prototype records."""
    records = research_repository.search(
        db,
        query=payload.query,
        source_type=payload.source_type.value if payload.source_type else None,
        jurisdiction=payload.jurisdiction,
        sort=payload.sort.value,
    )
    results = [_to_response(record) for record in records]
    return ResearchSearchResponse(
        query=payload.query,
        count=len(results),
        results=results,
        prototype=True,
    )


def get_result(db: Session, result_id: str) -> ResearchResultResponse:
    """Return a single prototype record or raise 404."""
    record = research_repository.get_result(db, result_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research record not found.",
        )
    return _to_response(record)


def _to_response(record: ResearchRecord) -> ResearchResultResponse:
    return ResearchResultResponse(
        result_id=record.id,
        title=record.title,
        source_type=record.source_type,
        jurisdiction=record.jurisdiction,
        date=record.date,
        citation_label=record.citation_label,
        summary=record.summary,
        topics=[str(topic) for topic in list(record.topics or [])],
        source_url=record.source_url,
        publisher=record.publisher,
        authority_level=record.authority_level,
        verified_at=record.verified_at.isoformat() if record.verified_at else None,
        prototype=bool(record.prototype),
    )


def retrieve_grounded(
    db: Session,
    query: str,
    understanding: LegalQueryUnderstanding | None = None,
    limit: int = 5,
) -> GroundedContext:
    """Run STEP 19 lexical retrieval over the canonical research records.

    Reads the exact same records used by the public research API
    (``research_repository.list_all``) — no duplicate table, no vector
    store, no external calls. Never fabricates sources; empty retrieval
    yields ``sources=[]`` / ``source_count=0`` / ``context_text=""``.
    """
    records = research_repository.list_all(db)
    grounded = research_retriever.retrieve(
        records, query=query, understanding=understanding, limit=limit
    )
    if not grounded.sources:
        return grounded

    source_ids = [source.source_id for source in grounded.sources]
    evidence_rows = (
        db.query(ResearchEvidence)
        .filter(ResearchEvidence.research_record_id.in_(source_ids))
        .order_by(ResearchEvidence.research_record_id.asc(), ResearchEvidence.id.asc())
        .all()
    )
    by_source: dict[str, list[RetrievedEvidencePassage]] = {}
    for row in evidence_rows:
        by_source.setdefault(row.research_record_id, []).append(
            RetrievedEvidencePassage(
                evidence_id=row.id,
                locator=row.locator,
                text=row.text,
            )
        )

    enriched_sources = [
        source.model_copy(update={"evidence": by_source.get(source.source_id, [])})
        for source in grounded.sources
    ]
    enriched_context = research_retriever.format_grounded_context(enriched_sources)
    return grounded.model_copy(
        update={
            "sources": enriched_sources,
            "context_text": enriched_context,
            "source_count": len(enriched_sources),
        }
    )
