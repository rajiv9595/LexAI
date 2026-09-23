"""Research application logic over persisted prototype records."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.models.query_understanding import LegalQueryUnderstanding
from app.ai.models.retrieval import GroundedContext
from app.ai.services import research_retriever
from app.models.research import ResearchRecord
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
        prototype=True,
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
    return research_retriever.retrieve(
        records, query=query, understanding=understanding, limit=limit
    )
