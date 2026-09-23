"""History routes. Prototype records scoped to authenticated user."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.history import HistoryItemResponse, HistoryListResponse
from app.services import history_service

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
def list_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryListResponse:
    """Return all persisted prototype history records belonging to the authenticated user."""
    return history_service.list_history(db, current_user.id)


@router.get("/{item_id}", response_model=HistoryItemResponse)
def read_history_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryItemResponse:
    """Return a single prototype record by id if owned by the authenticated user."""
    return history_service.get_history_item(db, item_id, current_user.id)
