"""Database architecture tests: metadata, relationships, seeding, persistence."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import Base
from app.data.seed import seed_database
from app.models.assistant import AssistantConversation


def test_metadata_contains_all_tables() -> None:
    tables = set(Base.metadata.tables.keys())
    assert {
        "documents",
        "assistant_conversations",
        "assistant_messages",
        "research_records",
        "history_items",
        "users",
    } <= tables


def test_conversation_messages_relationship(db: Session) -> None:
    conversation = db.get(AssistantConversation, "conversation-demo")
    assert conversation is not None
    assert len(conversation.messages) == 2
    assert conversation.messages[0].conversation is conversation


def test_seed_is_idempotent(db: Session) -> None:
    counts = seed_database(db)
    assert sum(counts.values()) == 0


def test_created_draft_persists_and_reads_back(auth_client: TestClient) -> None:
    created = auth_client.post(
        "/api/v1/documents",
        json={"type": "will", "details": {"testatorName": "Example Name"}},
    )
    assert created.status_code == 201
    document_id = created.json()["document_id"]
    fetched = auth_client.get(f"/api/v1/documents/{document_id}")
    assert fetched.status_code == 200
    assert fetched.json()["details"]["testatorName"] == "Example Name"


def test_posted_message_persists_in_conversation(auth_client: TestClient) -> None:
    posted = auth_client.post(
        "/api/v1/assistant/messages",
        json={"message": "Persistence check question?"},
    )
    assert posted.status_code == 200
    conversation_id = posted.json()["conversation_id"]
    fetched = auth_client.get(f"/api/v1/assistant/conversations/{conversation_id}")
    assert fetched.status_code == 200
    assert len(fetched.json()["messages"]) == 2
