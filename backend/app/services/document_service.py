"""Document application logic over persisted prototype drafts."""

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.documents import Document
from app.repositories import document_repository
from app.schemas.documents import (
    DocumentDraftRequest,
    DocumentDraftResponse,
    DocumentTemplateResponse,
    DocumentType,
)

_TEMPLATE_TITLES = {
    DocumentType.RENTAL: "Rental Agreement",
    DocumentType.EMPLOYMENT: "Employment Agreement",
    DocumentType.NDA: "Non-Disclosure Agreement",
    DocumentType.WILL: "Will / Testament",
}


def _format_date(document: Document) -> str:
    if document.created_at is None:
        return "Just now"
    return document.created_at.strftime("%b %d, %Y")


def list_templates() -> list[DocumentTemplateResponse]:
    """Return the prototype document templates."""
    return [
        DocumentTemplateResponse(
            type=item["type"],
            title=item["title"],
            description=item["description"],
            category=item["category"],
        )
        for item in document_repository.list_templates()
    ]


def list_documents(db: Session, user_id: str) -> list[DocumentDraftResponse]:
    """Return persisted prototype drafts belonging to the authenticated user."""
    return [
        _to_response(document)
        for document in document_repository.list_documents(db, user_id)
    ]


def get_document(
    db: Session, document_id: str, user_id: str
) -> DocumentDraftResponse:
    """Return a single prototype draft owned by user or raise 404."""
    document = document_repository.get_document(db, document_id, user_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return _to_response(document)


def create_draft(
    db: Session, user_id: str, payload: DocumentDraftRequest
) -> DocumentDraftResponse:
    """Create a user-owned prototype draft."""
    title = f"{_TEMPLATE_TITLES[payload.type]} Draft"
    try:
        document = document_repository.create_document(
            db, user_id, payload.type.value, title, dict(payload.details)
        )
        db.commit()
        db.refresh(document)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create the prototype draft.",
        ) from exc
    return _to_response(document)


def _to_response(document: Document) -> DocumentDraftResponse:
    return DocumentDraftResponse(
        document_id=document.id,
        type=DocumentType(document.type),
        title=document.title,
        status=document.status,
        created_date=_format_date(document),
        details={
            str(key): str(value)
            for key, value in dict(document.details or {}).items()
        },
        prototype=True,
    )
