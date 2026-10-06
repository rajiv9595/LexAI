"""Document request/response schemas for the user-owned document workspace."""

from datetime import datetime

from enum import Enum
from typing import Dict

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document workspace types."""

    RENTAL = "rental"
    EMPLOYMENT = "employment"
    NDA = "nda"
    WILL = "will"


class DocumentTemplateResponse(BaseModel):
    """Document template description."""

    type: DocumentType
    title: str
    description: str
    category: str


class DocumentDraftRequest(BaseModel):
    """Request to create a user-owned document draft."""

    type: DocumentType
    details: Dict[str, str] = Field(default_factory=dict)


class DocumentUpdateRequest(BaseModel):
    """Partial update for a user-owned document."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    details: Dict[str, str] | None = None


class DocumentDraftResponse(BaseModel):
    """Persisted user document payload."""

    document_id: str
    type: DocumentType
    title: str
    status: str = "Draft"
    created_date: str
    updated_date: str
    details: Dict[str, str] = Field(default_factory=dict)
    prototype: bool = False
