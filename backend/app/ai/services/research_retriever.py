"""Deterministic lexical research retriever (STEP 19 foundation).

Searches the existing curated research records and converts matches into
``RetrievedLegalSource`` items bundled as a ``GroundedContext``.

Design constraints (enforced here, not just documented):

- Provider-independent: no Gemini/OpenAI/embeddings/vector DB/external APIs.
- No fabrication: every field is copied from the canonical record. URLs,
  citations, dates, and jurisdictions are never invented. ``source_url``
  stays null because canonical records carry no URL field.
- No jurisdiction inference: only the explicit ``LegalQueryUnderstanding``
  jurisdiction is used (as an exact-match bonus). Null stays null.
- No legal conclusions: user statements are never rewritten into findings
  such as "violated rental law". Facts/dates/amounts/party names are NOT
  fed into the retrieval query.
- Transparent scoring: ``relevance_score`` means ONLY lexical relevance.

Scoring (per unique query term, substring match on lowercased fields):

- title match ............ +3.0 (high weight)
- topics match ........... +2.5 (high weight)
- summary match .......... +1.0 (medium weight)
- citation_label match ... +0.8 (lower weight)
- source_type exact signal +1.0 (term equals the record source_type)
- jurisdiction exact bonus +1.0 (explicit understanding jurisdiction only)

Ranking: score descending, then ``source_id`` ascending (deterministic
tie-break). Top N returned. Zero-score records are never returned.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from app.ai.models.query_understanding import LegalQueryUnderstanding
from app.ai.models.retrieval import (
    GroundedContext,
    RetrievedLegalSource,
    RetrievedSourceProvenance,
)

RETRIEVAL_METHOD = "lexical-weighted-v1"
DEFAULT_RETRIEVAL_LIMIT = 5
MAX_RETRIEVAL_LIMIT = 20

TITLE_WEIGHT = 3.0
TOPIC_WEIGHT = 2.5
SUMMARY_WEIGHT = 1.0
CITATION_WEIGHT = 0.8
SOURCE_TYPE_BONUS = 1.0
JURISDICTION_BONUS = 1.0

_NON_ALNUM = re.compile(r"[^a-z0-9]+")

STOPWORDS = frozenset(
    {
        "a", "about", "above", "after", "again", "against", "all", "am", "an",
        "and", "any", "are", "as", "at", "be", "because", "been", "before",
        "being", "below", "between", "both", "but", "by", "can", "cannot",
        "could", "did", "do", "does", "doing", "down", "during", "each",
        "few", "for", "from", "further", "had", "has", "have", "having",
        "he", "her", "here", "hers", "herself", "him", "himself", "his",
        "how", "i", "if", "in", "into", "is", "it", "its", "itself",
        "let", "me", "more", "most", "my", "myself", "no", "nor", "not",
        "of", "off", "on", "once", "only", "or", "other", "ought", "our",
        "ours", "same", "she", "should", "so", "some", "such", "than",
        "that", "the", "their", "theirs", "them", "themselves", "then",
        "there", "these", "they", "this", "those", "through", "to", "too",
        "under", "until", "up", "very", "was", "we", "were", "what",
        "when", "where", "which", "while", "who", "whom", "why", "with",
        "would", "you", "your", "yours", "yourself", "yourselves",
        "out", "got", "just", "like", "get", "also", "please", "tell",
        "want", "need", "know", "does", "done",
    }
)


def normalize_text(value: str | None) -> str:
    """Lowercase and collapse non-alphanumeric runs to single spaces."""
    if not value:
        return ""
    return _NON_ALNUM.sub(" ", value.lower()).strip()


def tokenize(text: str | None) -> list[str]:
    """Split normalized text into tokens, dropping stop words and 1-char tokens."""
    normalized = normalize_text(text)
    if not normalized:
        return []
    return [
        token
        for token in normalized.split()
        if len(token) > 1 and token not in STOPWORDS
    ]


def build_retrieval_terms(
    query: str,
    understanding: LegalQueryUnderstanding | None = None,
) -> list[str]:
    """Build a deterministic, legally focused retrieval term list.

    Sources (in order): raw query, ``primary_issue``, ``secondary_issues``,
    ``legal_domain`` (underscores become spaces). Duplicates are removed,
    preserving first-seen order.

    Deliberately EXCLUDED: user ``facts``, ``dates``, ``amounts``, party
    names, and any inferred jurisdiction. Jurisdiction is handled only as
    an explicit exact-match bonus in scoring — never as invented tokens.
    """
    parts: list[str] = [query or ""]
    if understanding is not None:
        if understanding.primary_issue:
            parts.append(understanding.primary_issue)
        for issue in understanding.secondary_issues or []:
            parts.append(issue)
        domain = (understanding.legal_domain or "").replace("_", " ")
        if domain and domain != "unknown":
            parts.append(domain)
    seen: set[str] = set()
    terms: list[str] = []
    for part in parts:
        for token in tokenize(part):
            if token not in seen:
                seen.add(token)
                terms.append(token)
    return terms


def _get_field(record: Any, name: str, default: Any = None) -> Any:
    if isinstance(record, Mapping):
        return record.get(name, default)
    return getattr(record, name, default)


def _extract_record_fields(record: Any) -> dict[str, Any]:
    """Copy canonical fields verbatim; never invent missing values."""
    record_id = (
        _get_field(record, "id", None)
        or _get_field(record, "result_id", None)
        or _get_field(record, "source_id", None)
        or ""
    )
    title = _get_field(record, "title", "") or ""
    source_type = _get_field(record, "source_type", "") or ""
    # source_type may be an enum (ResearchSourceType); coerce to its value.
    if not isinstance(source_type, str):
        source_type = getattr(source_type, "value", str(source_type))
    jurisdiction = _get_field(record, "jurisdiction", None)
    if isinstance(jurisdiction, str) and not jurisdiction.strip():
        jurisdiction = None
    date = _get_field(record, "date", "") or ""
    citation_label = _get_field(record, "citation_label", "") or ""
    summary = _get_field(record, "summary", "") or ""
    topics = _get_field(record, "topics", []) or []
    topics = [str(t) for t in list(topics)]
    prototype_raw = _get_field(record, "prototype", True)
    prototype = bool(prototype_raw) if prototype_raw is not None else True
    # Canonical records carry no URL field today; MUST stay null.
    source_url = _get_field(record, "source_url", None) or _get_field(
        record, "url", None
    )
    if isinstance(source_url, str) and not source_url.strip():
        source_url = None
    return {
        "record_id": str(record_id),
        "title": str(title),
        "source_type": str(source_type),
        "jurisdiction": jurisdiction,
        "date": str(date),
        "citation_label": str(citation_label),
        "summary": str(summary),
        "topics": topics,
        "prototype": prototype,
        "source_url": source_url,
    }


def score_record(
    fields: Mapping[str, Any],
    terms: Sequence[str],
    explicit_jurisdiction: str | None = None,
) -> float:
    """Calculate the deterministic lexical relevance score for one record."""
    title_l = str(fields.get("title", "")).lower()
    summary_l = str(fields.get("summary", "")).lower()
    topics_l = " ".join(str(t) for t in list(fields.get("topics", []) or [])).lower()
    citation_l = str(fields.get("citation_label", "")).lower()
    source_type_l = str(fields.get("source_type", "")).lower().replace("-", " ").strip()
    source_type_raw = str(fields.get("source_type", "")).lower().strip()

    score = 0.0
    for term in terms:
        if term in title_l:
            score += TITLE_WEIGHT
        if term in topics_l:
            score += TOPIC_WEIGHT
        if term in summary_l:
            score += SUMMARY_WEIGHT
        if term in citation_l:
            score += CITATION_WEIGHT
        if term == source_type_l or term == source_type_raw:
            score += SOURCE_TYPE_BONUS
    jurisdiction = fields.get("jurisdiction")
    if (
        explicit_jurisdiction
        and isinstance(jurisdiction, str)
        and jurisdiction.strip()
        and jurisdiction.strip().lower() == explicit_jurisdiction.strip().lower()
    ):
        score += JURISDICTION_BONUS
    return round(score, 4)


def _to_retrieved_source(fields: Mapping[str, Any], score: float) -> RetrievedLegalSource:
    jurisdiction = fields.get("jurisdiction")
    return RetrievedLegalSource(
        source_id=str(fields.get("record_id", "")),
        title=str(fields.get("title", "")),
        source_type=str(fields.get("source_type", "")),
        jurisdiction=jurisdiction,
        date=str(fields.get("date", "")),
        citation_label=str(fields.get("citation_label", "")),
        summary=str(fields.get("summary", "")),
        topics=list(fields.get("topics", []) or []),
        relevance_score=float(score),
        provenance=RetrievedSourceProvenance(
            source_record_id=str(fields.get("record_id", "")),
            source_kind=str(fields.get("source_type", "")),
            source_url=fields.get("source_url"),
            citation_label=str(fields.get("citation_label", "")),
            prototype=bool(fields.get("prototype", True)),
        ),
        prototype=bool(fields.get("prototype", True)),
    )


def format_grounded_context(sources: Sequence[RetrievedLegalSource]) -> str:
    """Render retrieved sources deterministically; empty list -> empty string."""
    if not sources:
        return ""
    blocks: list[str] = []
    for index, source in enumerate(sources, start=1):
        jurisdiction = source.jurisdiction if source.jurisdiction else "unknown"
        prototype_flag = "true" if source.prototype else "false"
        blocks.append(
            "SOURCE {}\n"
            "Title: {}\n"
            "Source Type: {}\n"
            "Jurisdiction: {}\n"
            "Date: {}\n"
            "Citation: {}\n"
            "Prototype: {}\n"
            "Summary: {}".format(
                index,
                source.title,
                source.source_type,
                jurisdiction,
                source.date,
                source.citation_label,
                prototype_flag,
                source.summary,
            )
        )
    return "\n\n".join(blocks)


def retrieve(
    records: Sequence[Any],
    query: str,
    understanding: LegalQueryUnderstanding | None = None,
    limit: int = DEFAULT_RETRIEVAL_LIMIT,
) -> GroundedContext:
    """Run deterministic lexical retrieval over canonical record objects.

    Args:
        records: canonical research records (ORM objects, response models,
            or plain dicts). The same objects used by the public research API.
        query: original user query text.
        understanding: optional ``LegalQueryUnderstanding`` output used to
            focus the retrieval terms. Its jurisdiction is used ONLY as an
            explicit exact-match signal; a null jurisdiction is never inferred.
        limit: maximum sources to return (clamped to 1..20; <=0 -> empty).

    Returns:
        ``GroundedContext`` with ranked sources, formatted ``context_text``,
        and ``retrieval_method`` = ``lexical-weighted-v1``. Empty retrieval
        yields ``sources=[]``, ``source_count=0``, ``context_text=""``.
    """
    normalized_query = (query or "").strip()
    if limit <= 0:
        return GroundedContext(
            query=normalized_query,
            sources=[],
            context_text="",
            source_count=0,
            retrieval_method=RETRIEVAL_METHOD,
            generated_at=datetime.now(timezone.utc),
        )
    effective_limit = max(1, min(int(limit), MAX_RETRIEVAL_LIMIT))
    terms = build_retrieval_terms(normalized_query, understanding)
    if not terms:
        return GroundedContext(
            query=normalized_query,
            sources=[],
            context_text="",
            source_count=0,
            retrieval_method=RETRIEVAL_METHOD,
            generated_at=datetime.now(timezone.utc),
        )
    explicit_jurisdiction = None
    if understanding is not None and understanding.jurisdiction:
        explicit_jurisdiction = understanding.jurisdiction

    scored: list[tuple[float, str, dict[str, Any]]] = []
    for record in records or []:
        fields = _extract_record_fields(record)
        if not fields["record_id"]:
            continue
        score = score_record(fields, terms, explicit_jurisdiction)
        if score > 0:
            scored.append((score, fields["record_id"], fields))
    # Rank: score descending, then source_id ascending (deterministic tie-break).
    scored.sort(key=lambda item: (-item[0], item[1]))
    selected = scored[:effective_limit]
    sources = [_to_retrieved_source(fields, score) for score, _, fields in selected]
    context_text = format_grounded_context(sources)
    return GroundedContext(
        query=normalized_query,
        sources=sources,
        context_text=context_text,
        source_count=len(sources),
        retrieval_method=RETRIEVAL_METHOD,
        generated_at=datetime.now(timezone.utc),
    )


def grounded_context_to_chunks(context: GroundedContext | None) -> list[str]:
    """Convert a ``GroundedContext`` into ``AIRequest.retrieved_context`` chunks.

    Empty retrieval -> ``[]`` (never fabricated fallback text).
    """
    if context is None or not context.sources or not context.context_text:
        return []
    return [context.context_text]


# Type alias for orchestrator dependency injection: a DB-backed resolver that
# maps (query, understanding) -> GroundedContext without coupling the
# orchestrator itself to FastAPI/SQLAlchemy.
RetrievalResolver = Callable[[str, LegalQueryUnderstanding | None], GroundedContext]
