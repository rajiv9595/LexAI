"""Document routes. Prototype drafts scoped to authenticated user."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.documents import (
    DocumentDraftRequest,
    DocumentDraftResponse,
    DocumentTemplateResponse,
)
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/templates", response_model=list[DocumentTemplateResponse])
def list_templates() -> list[DocumentTemplateResponse]:
    """Return the prototype document templates."""
    return document_service.list_templates()


@router.get("", response_model=list[DocumentDraftResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentDraftResponse]:
    """Return persisted prototype drafts belonging to the authenticated user."""
    return document_service.list_documents(db, current_user.id)


@router.get("/{document_id}", response_model=DocumentDraftResponse)
def read_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDraftResponse:
    """Return a single prototype draft by id if owned by the authenticated user."""
    return document_service.get_document(db, document_id, current_user.id)


@router.post("", response_model=DocumentDraftResponse, status_code=201)
def create_document(
    payload: DocumentDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDraftResponse:
    """Create a persisted prototype draft owned by the authenticated user."""
    return document_service.create_draft(db, current_user.id, payload)
