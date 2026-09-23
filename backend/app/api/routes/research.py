"""Research routes. Persisted prototype records only; no external search."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.research import (
    ResearchResultResponse,
    ResearchSearchRequest,
    ResearchSearchResponse,
)
from app.services import research_service

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/search", response_model=ResearchSearchResponse)
def search_research(
    payload: ResearchSearchRequest, db: Session = Depends(get_db)
) -> ResearchSearchResponse:
    """Run a deterministic local search over persisted prototype records."""
    return research_service.search_prototype(db, payload)


@router.get("/{result_id}", response_model=ResearchResultResponse)
def read_result(
    result_id: str, db: Session = Depends(get_db)
) -> ResearchResultResponse:
    """Return a single prototype record by id."""
    return research_service.get_result(db, result_id)
