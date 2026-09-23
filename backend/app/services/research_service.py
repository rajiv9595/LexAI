"""Research application logic over persisted prototype records."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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
