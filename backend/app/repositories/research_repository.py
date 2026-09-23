"""Research data access through SQLAlchemy sessions."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.research import ResearchRecord


def _matches(record: ResearchRecord, tokens: list[str]) -> bool:
    haystack = " ".join(
        [
            record.title,
            record.summary,
            " ".join(record.topics or []),
            record.jurisdiction,
            record.source_type.replace("-", " "),
        ]
    ).lower()
    return all(token in haystack for token in tokens)


def _parse_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%b %d, %Y").isoformat()
    except ValueError:
        return ""


def search(
    db: Session,
    query: str,
    source_type: str | None = None,
    jurisdiction: str | None = None,
    sort: str = "relevance",
) -> list[ResearchRecord]:
    """Deterministic local search over persisted prototype records."""
    tokens = [token for token in query.strip().lower().split() if len(token) > 1]
    candidates = db.query(ResearchRecord).all()
    matched = [
        record
        for record in candidates
        if (not source_type or record.source_type == source_type)
        and (not jurisdiction or record.jurisdiction == jurisdiction)
        and (not tokens or _matches(record, tokens))
    ]
    if sort == "date":
        matched.sort(key=lambda item: _parse_date(item.date), reverse=True)
    return matched


def get_result(db: Session, result_id: str) -> ResearchRecord | None:
    """Return a single prototype record, if it exists."""
    return db.get(ResearchRecord, result_id)
