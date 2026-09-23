"""Strongly typed retrieval models for grounded legal-research context.

STEP 19 — Legal research retrieval & grounded-context foundation.

These models describe *copied* material from the existing curated research
records already present in LexAssist. They are evidence containers only:

- No legal conclusions are produced here.
- No citations, URLs, dates, or jurisdictions are invented.
- ``relevance_score`` means ONLY lexical relevance to the query, never
  legal authority.
- ``prototype`` records remain explicitly marked; prototype material must
  never be presented as verified external legal authority.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class RetrievedSourceProvenance(BaseModel):
    """Structured provenance for a single retrieved research record."""

    source_record_id: str = Field(
        ..., description="Stable identifier of the canonical research record"
    )
    source_kind: str = Field(
        ..., description="Controlled source type copied from the record"
    )
    source_url: str | None = Field(
        default=None,
        description=(
            "External URL only when the canonical record actually has one; "
            "null otherwise. Never fabricated."
        ),
    )
    citation_label: str = Field(
        ..., description="Citation label copied verbatim from the record"
    )
    prototype: bool = Field(
        default=True,
        description="True when the underlying record is prototype/demo material",
    )


class RetrievedLegalSource(BaseModel):
    """A single retrieved legal-evidence item copied from a research record."""

    source_id: str = Field(..., description="Stable id of the research record")
    title: str = Field(..., description="Record title copied verbatim")
    source_type: str = Field(..., description="Controlled source type copied verbatim")
    jurisdiction: str | None = Field(
        default=None,
        description="Record jurisdiction, or null when unavailable",
    )
    date: str = Field(default="", description="Record date copied verbatim")
    citation_label: str = Field(
        ..., description="Citation label copied verbatim; never fabricated"
    )
    summary: str = Field(..., description="Record summary copied verbatim")
    topics: list[str] = Field(
        default_factory=list, description="Record topics copied verbatim"
    )
    relevance_score: float = Field(
        ..., ge=0.0, description="Deterministic lexical relevance score only"
    )
    provenance: RetrievedSourceProvenance = Field(
        ..., description="Source provenance; source_url is null unless the record has one"
    )
    prototype: bool = Field(
        default=True,
        description="Preserved prototype flag from the canonical record",
    )


class GroundedContext(BaseModel):
    """Deterministic grounded context supplied to the AI layer as evidence.

    This is NOT a legal conclusion. It is retrieved source material that a
    future grounded-answer layer (STEP 20) may use. An empty ``sources``
    list means "no relevant research record retrieved" and must not be
    replaced with fabricated fallback sources.
    """

    query: str = Field(..., description="Retrieval query text used")
    sources: list[RetrievedLegalSource] = Field(
        default_factory=list, description="Ranked retrieved sources"
    )
    context_text: str = Field(
        default="",
        description="Deterministic formatted representation of sources; empty when none",
    )
    source_count: int = Field(
        default=0, description="Number of retrieved sources (len(sources))"
    )
    retrieval_method: str = Field(
        default="lexical-weighted-v1",
        description="Deterministic retrieval algorithm identifier",
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the grounded context was built",
    )
