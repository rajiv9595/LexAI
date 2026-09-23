"""Explicit development seed for prototype/demo records.

Run once after migrations:

    python -m app.data.seed

Inserts prototype data only. No users, no credentials, no authoritative
legal information. Fails clearly if the database is unavailable; never
falls back to mock data silently.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.documents import Document
from app.models.history import HistoryItem
from app.models.research import ResearchRecord

SEED_CONVERSATION_ID = "conversation-demo"
SEED_DOCUMENT_ID = "rental-agreement-demo"


def _utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def seed_database(db: Session) -> dict[str, int]:
    """Insert prototype records if they are not already present."""
    counts = {"conversations": 0, "messages": 0, "documents": 0, "research": 0, "history": 0}

    if db.get(AssistantConversation, SEED_CONVERSATION_ID) is None:
        conversation = AssistantConversation(id=SEED_CONVERSATION_ID, prototype=True)
        db.add(conversation)
        db.add(
            AssistantMessage(
                id="message-demo-1",
                conversation_id=SEED_CONVERSATION_ID,
                role="user",
                content="I rented a house and my landlord is refusing to return my security deposit after I moved out. What should I do?",
                prototype=True,
            )
        )
        db.add(
            AssistantMessage(
                id="message-demo-2",
                conversation_id=SEED_CONVERSATION_ID,
                role="assistant",
                content="LexAssist prototype response: this demonstration conversation shows how a rental-deposit concern could be structured. Real AI-assisted legal analysis will be connected in a later integration step.",
                prototype=True,
            )
        )
        counts["conversations"] = 1
        counts["messages"] = 2

    if db.get(Document, SEED_DOCUMENT_ID) is None:
        db.add(
            Document(
                id=SEED_DOCUMENT_ID,
                type="rental",
                title="Rental Agreement Draft",
                status="Prototype Draft",
                details={
                    "landlordName": "Rajiv Reddy",
                    "tenantName": "Example Tenant",
                    "propertyAddress": "Example Address",
                },
                prototype=True,
                created_at=_utc(2026, 9, 20),
                updated_at=_utc(2026, 9, 20),
            )
        )
        counts["documents"] = 1

    research_seed = [
        ("rental-deposit-dispute", "Rental Deposit Dispute — Prototype Research Record", "case", "Demo case record",
         "A demonstration record showing how rental-deposit issues could be organized for legal research.",
         ["Rental housing", "Security deposit", "Tenant rights"], "Sep 20, 2026"),
        ("employment-termination", "Employment Termination — Prototype Research Record", "precedent", "Prototype reference",
         "A demonstration record showing how employment-ending scenarios could be organized for legal research.",
         ["Employment", "Termination procedures", "Workplace rights"], "Sep 12, 2026"),
        ("confidentiality-obligations", "Confidentiality Obligations — Prototype Research Record", "regulation", "Prototype reference",
         "A demonstration record showing how confidentiality duties could be organized for legal research.",
         ["Confidentiality", "Business agreements", "Disclosure duties"], "Aug 28, 2026"),
        ("property-ownership-dispute", "Property Ownership Dispute — Prototype Research Record", "statute", "General reference",
         "A demonstration record showing how property-ownership questions could be organized for legal research.",
         ["Property ownership", "Title records", "Boundary questions"], "Aug 15, 2026"),
        ("contract-review-basics", "Contract Review Basics — Prototype Research Record", "general-reference", "General reference",
         "A demonstration record showing how contract-review topics could be organized for legal research.",
         ["Contracts", "Review checklist", "Signatures"], "Jul 30, 2026"),
    ]
    for record_id, title, source_type, citation, summary, topics, date in research_seed:
        if db.get(ResearchRecord, record_id) is None:
            db.add(
                ResearchRecord(
                    id=record_id,
                    title=title,
                    source_type=source_type,
                    jurisdiction="Prototype / General",
                    date=date,
                    citation_label=citation,
                    summary=summary,
                    topics=list(topics),
                    prototype=True,
                )
            )
            counts["research"] += 1

    history_seed = [
        ("history-rental-deposit-session", "assistant", "Rental Deposit Question",
         "Prototype assistant session demonstrating structured legal issue analysis.",
         "Rental / Housing", "completed", "Sep 21, 2026", "/app/assistant"),
        ("history-rental-agreement-draft", "document", "Rental Agreement Draft",
         "Prototype document draft demonstrating the guided document workflow.",
         "Tenancy", "draft", "Sep 20, 2026", "/app/documents/rental-agreement-demo"),
        ("history-security-deposit-research", "research", "Security Deposit Dispute Research",
         "Prototype research activity demonstrating organized legal references.",
         "Rental / Housing", "prototype", "Sep 20, 2026", "/app/research"),
    ]
    for item_id, item_type, title, description, category, status, updated, route in history_seed:
        if db.get(HistoryItem, item_id) is None:
            db.add(
                HistoryItem(
                    id=item_id,
                    item_type=item_type,
                    title=title,
                    description=description,
                    category=category,
                    status=status,
                    updated_at=updated,
                    related_route=route,
                    item_metadata={},
                    prototype=True,
                )
            )
            counts["history"] += 1

    db.commit()
    return counts


def main() -> None:
    """Seed entry point. Raises clearly if the database is unreachable."""
    try:
        db = SessionLocal()
    except Exception as exc:
        raise RuntimeError(f"Could not connect to the database: {exc}") from exc
    try:
        counts = seed_database(db)
    finally:
        db.close()
    total = sum(counts.values())
    print(f"Seed complete. Inserted {total} prototype records: {counts}")


if __name__ == "__main__":
    main()
