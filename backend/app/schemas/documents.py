"""Document request/response schemas."""

from enum import Enum
from typing import Dict

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported prototype document templates."""

    RENTAL = "rental"
    EMPLOYMENT = "employment"
    NDA = "nda"
    WILL = "will"


class DocumentTemplateResponse(BaseModel):
    """Prototype document template description."""

    type: DocumentType
    title: str
    description: str
    category: str


class DocumentDraftRequest(BaseModel):
    """Request to create an in-memory prototype draft."""

    type: DocumentType
    details: Dict[str, str] = Field(default_factory=dict)


class DocumentDraftResponse(BaseModel):
    """Prototype draft payload. Not a legally valid document."""

    document_id: str
    type: DocumentType
    title: str
    status: str = "Prototype Draft"
    created_date: str
    details: Dict[str, str] = Field(default_factory=dict)
    prototype: bool = True
