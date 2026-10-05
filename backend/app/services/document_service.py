"""Document application services for the user-owned document workspace."""

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
    DocumentUpdateRequest,
)

_TEMPLATE_TITLES = {
    DocumentType.RENTAL: "Rental Agreement",
    DocumentType.EMPLOYMENT: "Employment Agreement",
    DocumentType.NDA: "Non-Disclosure Agreement",
    DocumentType.WILL: "Will / Testament",
}


def _format_date(value) -> str:
    if value is None:
        return ""
    return value.isoformat()


def list_templates() -> list[DocumentTemplateResponse]:
    """Return the document template catalog."""
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
    """Return persisted user-owned documents."""
    return [_to_response(document) for document in document_repository.list_documents(db, user_id)]


def get_document(
    db: Session, document_id: str, user_id: str
) -> DocumentDraftResponse:
    """Return a single user-owned document or raise 404."""
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
    """Create a persistent user-owned document."""
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
            detail="Could not create the document.",
        ) from exc
    return _to_response(document)


def update_document(
    db: Session,
    user_id: str,
    document_id: str,
    payload: DocumentUpdateRequest,
) -> DocumentDraftResponse:
    """Update a user-owned document."""
    if payload.title is None and payload.details is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one document field must be supplied.",
        )

    try:
        document = document_repository.update_document(
            db,
            document_id,
            user_id,
            title=payload.title,
            details=payload.details,
        )
        if document is None:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )
        db.commit()
        db.refresh(document)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update the document.",
        ) from exc

    return _to_response(document)


def delete_document(db: Session, user_id: str, document_id: str) -> None:
    """Delete a user-owned document."""
    try:
        deleted = document_repository.delete_document(db, document_id, user_id)
        if not deleted:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )
        db.commit()
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete the document.",
        ) from exc


def _to_response(document: Document) -> DocumentDraftResponse:
    return DocumentDraftResponse(
        document_id=document.id,
        type=DocumentType(document.type),
        title=document.title,
        status=document.status,
        created_date=_format_date(document.created_at),
        updated_date=_format_date(document.updated_at),
        details={str(key): str(value) for key, value in dict(document.details or {}).items()},
        prototype=bool(document.prototype),
    )
