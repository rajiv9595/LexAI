"""Document routes for the authenticated document workspace."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.documents import (
    DocumentDraftRequest,
    DocumentDraftResponse,
    DocumentTemplateResponse,
    DocumentUpdateRequest,
)
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/templates", response_model=list[DocumentTemplateResponse])
def list_templates() -> list[DocumentTemplateResponse]:
    """Return the available document templates."""
    return document_service.list_templates()


@router.get("", response_model=list[DocumentDraftResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentDraftResponse]:
    """Return documents belonging to the authenticated user."""
    return document_service.list_documents(db, current_user.id)


@router.get("/{document_id}", response_model=DocumentDraftResponse)
def read_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDraftResponse:
    """Return one user-owned document."""
    return document_service.get_document(db, document_id, current_user.id)


@router.post("", response_model=DocumentDraftResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDraftResponse:
    """Create a new user-owned document."""
    return document_service.create_draft(db, current_user.id, payload)


@router.patch("/{document_id}", response_model=DocumentDraftResponse)
def update_document(
    document_id: str,
    payload: DocumentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDraftResponse:
    """Update a user-owned document."""
    return document_service.update_document(db, current_user.id, document_id, payload)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a user-owned document."""
    document_service.delete_document(db, current_user.id, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
