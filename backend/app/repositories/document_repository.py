"""Document data access through SQLAlchemy sessions."""

from sqlalchemy.orm import Session

from app.data import mock_data
from app.models.documents import Document


def list_documents(db: Session, user_id: str) -> list[Document]:
    """Return all prototype document drafts belonging to the user."""
    return list(
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .all()
    )


def get_document(db: Session, document_id: str, user_id: str) -> Document | None:
    """Return a single prototype draft if owned by the user."""
    return (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )


def create_document(
    db: Session, user_id: str, document_type: str, title: str, details: dict[str, str]
) -> Document:
    """Stage a new prototype draft belonging to the user in the transaction."""
    prefix = f"session-{document_type}-draft"
    existing = (
        db.query(Document).filter(Document.id.like(f"{prefix}%")).count()
    )
    document = Document(
        id=f"{prefix}-{existing + 1}",
        type=document_type,
        title=title,
        status="Prototype Draft",
        details=dict(details),
        prototype=True,
        user_id=user_id,
    )
    db.add(document)
    db.flush()
    return document


def list_templates() -> list[dict[str, str]]:
    """Return the static prototype template catalog (not persisted)."""
    return [dict(item) for item in mock_data.DOCUMENT_TEMPLATES]
