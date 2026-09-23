"""History data access through SQLAlchemy sessions."""

from sqlalchemy.orm import Session

from app.models.history import HistoryItem


def list_items(db: Session, user_id: str) -> list[HistoryItem]:
    """Return all prototype history records belonging to the user."""
    return list(
        db.query(HistoryItem)
        .filter(HistoryItem.user_id == user_id)
        .order_by(HistoryItem.created_at.desc())
        .all()
    )


def get_item(db: Session, item_id: str, user_id: str) -> HistoryItem | None:
    """Return a single prototype record if owned by the user."""
    return (
        db.query(HistoryItem)
        .filter(HistoryItem.id == item_id, HistoryItem.user_id == user_id)
        .first()
    )
