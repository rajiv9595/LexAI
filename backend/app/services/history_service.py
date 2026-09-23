"""History application logic over persisted prototype records."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.history import HistoryItem
from app.repositories import history_repository
from app.schemas.history import HistoryItemResponse, HistoryListResponse


def list_history(db: Session, user_id: str) -> HistoryListResponse:
    """Return all persisted prototype history records belonging to the user."""
    items = [
        _to_response(item) for item in history_repository.list_items(db, user_id)
    ]
    return HistoryListResponse(count=len(items), items=items, prototype=True)


def get_history_item(
    db: Session, item_id: str, user_id: str
) -> HistoryItemResponse:
    """Return a single prototype record owned by the user or raise 404."""
    item = history_repository.get_item(db, item_id, user_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History item not found.",
        )
    return _to_response(item)


def _to_response(item: HistoryItem) -> HistoryItemResponse:
    return HistoryItemResponse(
        item_id=item.id,
        type=item.item_type,
        title=item.title,
        description=item.description,
        category=item.category,
        status=item.status.lower(),
        updated_at=item.updated_at,
        related_route=item.related_route,
        prototype=True,
    )
