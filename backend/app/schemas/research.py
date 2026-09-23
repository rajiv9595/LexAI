"""Research request/response schemas."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ResearchSourceType(str, Enum):
    """Supported prototype research source types."""

    STATUTE = "statute"
    CASE = "case"
    PRECEDENT = "precedent"
    REGULATION = "regulation"
    GENERAL_REFERENCE = "general-reference"


class ResearchSort(str, Enum):
    """Supported result orderings."""

    RELEVANCE = "relevance"
    DATE = "date"


class ResearchSearchRequest(BaseModel):
    """Prototype research search input."""

    query: str = Field(default="", max_length=500)
    source_type: Optional[ResearchSourceType] = None
    jurisdiction: Optional[str] = Field(default=None, max_length=128)
    sort: ResearchSort = ResearchSort.RELEVANCE


class ResearchResultResponse(BaseModel):
    """Single prototype research record. Not an authoritative source."""

    result_id: str
    title: str
    source_type: ResearchSourceType
    jurisdiction: str
    date: str
    citation_label: str
    summary: str
    topics: List[str] = Field(default_factory=list)
    prototype: bool = True


class ResearchSearchResponse(BaseModel):
    """Deterministic prototype search payload."""

    query: str
    count: int
    results: List[ResearchResultResponse] = Field(default_factory=list)
    prototype: bool = True
