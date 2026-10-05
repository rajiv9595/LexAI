"""Document data access through SQLAlchemy sessions."""

from uuid import uuid4

from sqlalchemy.orm import Session

from app.data import mock_data
from app.models.documents import Document


def list_documents(db: Session, user_id: str) -> list[Document]:
    """Return user-owned documents ordered by latest activity."""
    return list(
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.updated_at.desc(), Document.id.desc())
        .all()
    )


def get_document(db: Session, document_id: str, user_id: str) -> Document | None:
    """Return a document only when it belongs to the authenticated user."""
    return (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )


def create_document(
    db: Session,
    user_id: str,
    document_type: str,
    title: str,
    details: dict[str, str],
) -> Document:
    """Stage a new user-owned document in the current transaction."""
    document = Document(
        id=f"document-{uuid4().hex}",
        type=document_type,
        title=title,
        status="Draft",
        details=dict(details),
        prototype=False,
        user_id=user_id,
    )
    db.add(document)
    db.flush()
    return document


def update_document(
    db: Session,
    document_id: str,
    user_id: str,
    *,
    title: str | None = None,
    details: dict[str, str] | None = None,
) -> Document | None:
    """Update a user-owned document in the current transaction."""
    document = get_document(db, document_id, user_id)
    if document is None:
        return None

    if title is not None:
        document.title = title.strip()
    if details is not None:
        document.details = dict(details)

    db.flush()
    return document


def delete_document(db: Session, document_id: str, user_id: str) -> bool:
    """Delete a user-owned document in the current transaction."""
    document = get_document(db, document_id, user_id)
    if document is None:
        return False

    db.delete(document)
    db.flush()
    return True


def list_templates() -> list[dict[str, str]]:
    """Return the application document template catalog."""
    return [dict(item) for item in mock_data.DOCUMENT_TEMPLATES]
