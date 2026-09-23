"""Deterministic citation/reference validator (STEP 20 grounded answers).

Validates Gemini-generated references against the actual ``GroundedContext``
source of truth. Pure and provider-independent: no LLM calls, no network
access, no database access.

Policy (deterministic, no guessing):

- The allowlist (source ids + citation labels) is built dynamically from
  the supplied ``GroundedContext`` — never hard-coded.
- ``GroundedContext.source_count == 0`` (or ``None``) → ``references == []``.
- A candidate reference binds to a retrieved source by ``source_id`` first,
  then by ``citation`` label. A candidate matching neither is rejected.
- A candidate whose ``source_id`` is known but whose non-empty ``citation``
  does not equal that source's ``citation_label`` is rejected (prevents
  attaching a fabricated citation to a real source id).
- Valid references are REBUILT from backend metadata (title, kind from
  source_type, citation from citation_label, jurisdiction, prototype).
  Only the model's ``relevance_note`` is preserved, with URL-like tokens
  sanitized out so uninvented URLs can never surface through references.
- Mixed valid/invalid input keeps the valid entries in stable order;
  invalid entries are dropped, never replaced or remapped.
- Duplicates (same ``source_id``) are collapsed, preserving first-seen order.

What this does NOT do: it confirms reference *provenance* (cited ids/labels
correspond to retrieved records). It does not independently establish the
legal correctness of the generated prose.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from app.ai.models.responses import LegalAssistantResponse, LegalReferenceItem
from app.ai.models.retrieval import GroundedContext, RetrievedLegalSource

# URL-like tokens are never legitimate inside a validated reference note.
_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# Single deterministic notice appended when every cited source is prototype
# material, so prototype status is communicated even if the model omits it.
ALL_PROTOTYPE_NOTICE = (
    "[Note: the cited source(s) are curated prototype research records for "
    "informational purposes, not verified legal authority.]"
)


class CitationValidationResult(BaseModel):
    """Structured outcome of deterministic citation validation."""

    response: LegalAssistantResponse = Field(
        ..., description="Response copy carrying only validated references"
    )
    allowed_source_ids: list[str] = Field(
        default_factory=list,
        description="Source ids admitted from the supplied GroundedContext",
    )
    kept_count: int = Field(default=0, description="References retained")
    removed_count: int = Field(default=0, description="References rejected")


def build_allowlist(
    grounded: GroundedContext | None,
) -> dict[str, RetrievedLegalSource]:
    """Map allowed ``source_id`` -> retrieved source from the grounded context."""
    if grounded is None or not grounded.sources:
        return {}
    allowlist: dict[str, RetrievedLegalSource] = {}
    for source in grounded.sources:
        allowlist.setdefault(source.source_id, source)
    return allowlist


def _sanitize_note(note: str | None) -> str:
    """Remove URL-like tokens from a model-supplied relevance note."""
    if not note:
        return ""
    return _URL_PATTERN.sub("[removed]", str(note)).strip()


def _rebuild_reference(
    source: RetrievedLegalSource, relevance_note: str
) -> LegalReferenceItem:
    """Rebuild a reference from backend metadata (never trust model metadata)."""
    return LegalReferenceItem(
        title=source.title,
        kind=source.source_type,
        citation=source.citation_label,
        relevance_note=_sanitize_note(relevance_note),
        source_id=source.source_id,
        jurisdiction=source.jurisdiction,
        prototype=source.prototype,
    )


def _resolve_candidate(
    candidate: Mapping[str, Any] | LegalReferenceItem,
    allowlist: dict[str, RetrievedLegalSource],
) -> RetrievedLegalSource | None:
    """Bind one candidate reference to an allowlisted source, if possible."""
    if isinstance(candidate, LegalReferenceItem):
        raw_id = (candidate.source_id or "").strip()
        raw_citation = (candidate.citation or "").strip()
        raw_note = candidate.relevance_note or ""
    else:
        raw_id = str(candidate.get("source_id", "") or "").strip()
        raw_citation = str(candidate.get("citation", "") or "").strip()
        raw_note = candidate.get("relevance_note", "") or ""
    _ = raw_note  # note is applied at rebuild time, not during resolution

    if raw_id:
        source = allowlist.get(raw_id)
        if source is None:
            return None
        if raw_citation and raw_citation != source.citation_label:
            # Real id paired with a foreign/fabricated citation: reject.
            return None
        return source
    if raw_citation:
        matches = [
            source
            for sid, source in sorted(allowlist.items())
            if source.citation_label == raw_citation
        ]
        return matches[0] if matches else None
    return None


def validate_references(
    candidates: list[LegalReferenceItem | dict[str, Any]] | None,
    grounded: GroundedContext | None,
) -> tuple[list[LegalReferenceItem], int]:
    """Validate candidate references; return (validated, removed_count).

    Deterministic and side-effect free. Empty grounded context always yields
    an empty validated list.
    """
    allowlist = build_allowlist(grounded)
    if not allowlist or not candidates:
        removed = len(candidates or [])
        return [], removed
    validated: list[LegalReferenceItem] = []
    seen: set[str] = set()
    removed = 0
    for candidate in candidates:
        source = _resolve_candidate(candidate, allowlist)
        if source is None:
            removed += 1
            continue
        if source.source_id in seen:
            # Duplicate of an already-kept source: collapse silently
            # without counting it as a rejected fabrication.
            continue
        seen.add(source.source_id)
        note = (
            candidate.relevance_note
            if isinstance(candidate, LegalReferenceItem)
            else candidate.get("relevance_note", "")
        )
        validated.append(_rebuild_reference(source, note or ""))
    return validated, removed


def validate_response_citations(
    response: LegalAssistantResponse,
    grounded: GroundedContext | None,
) -> CitationValidationResult:
    """Return a validated copy of a final assistant response.

    - References are validated/rebuilt against ``grounded``.
    - When validated references are non-empty and EVERY retrieved source is
      prototype material, a single prototype-limitation notice is appended
      to the answer (once) so the limitation is communicated.
    - All other response fields pass through unchanged.
    """
    allowlist = build_allowlist(grounded)
    validated_refs, removed = validate_references(
        list(response.references or []), grounded
    )
    answer = response.answer
    if (
        validated_refs
        and grounded is not None
        and grounded.sources
        and all(source.prototype for source in grounded.sources)
        and ALL_PROTOTYPE_NOTICE not in answer
    ):
        answer = f"{answer}\n\n{ALL_PROTOTYPE_NOTICE}"
    validated = response.model_copy(
        update={"answer": answer, "references": validated_refs}
    )
    return CitationValidationResult(
        response=validated,
        allowed_source_ids=sorted(allowlist.keys()),
        kept_count=len(validated_refs),
        removed_count=removed,
    )
