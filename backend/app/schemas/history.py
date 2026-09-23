"""History request/response schemas."""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class HistoryItemType(str, Enum):
    """Prototype activity kinds."""

    ASSISTANT = "assistant"
    DOCUMENT = "document"
    RESEARCH = "research"


class HistoryStatus(str, Enum):
    """Prototype activity statuses."""

    PROTOTYPE = "prototype"
    DRAFT = "draft"
    COMPLETED = "completed"


class HistoryItemResponse(BaseModel):
    """Single prototype workspace activity record."""

    item_id: str
    type: HistoryItemType
    title: str
    description: str
    category: str
    status: HistoryStatus
    updated_at: str
    related_route: str
    prototype: bool = True


class HistoryListResponse(BaseModel):
    """Prototype activity list payload."""

    count: int
    items: List[HistoryItemResponse] = Field(default_factory=list)
    prototype: bool = True
