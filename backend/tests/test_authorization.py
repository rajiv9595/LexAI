"""Comprehensive authorization and cross-user data isolation tests."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.assistant import AssistantConversation
from app.models.documents import Document
from app.models.history import HistoryItem
from app.models.research import ResearchRecord
from app.repositories import user_repository


def _create_user(db: Session, email: str, name: str):
    user = user_repository.create(
        db=db,
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=name,
    )
    db.commit()
    db.refresh(user)
    return user


def _get_auth_headers(user_id: str) -> dict[str, str]:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Cross-User Isolation Tests (User A vs User B)
# ---------------------------------------------------------------------------


def test_cross_user_document_isolation(client: TestClient, db: Session) -> None:
    """User A creates a document; User B cannot list or access it."""
    user_a = _create_user(db, "usera.doc@example.com", "User A")
    user_b = _create_user(db, "userb.doc@example.com", "User B")
    headers_a = _get_auth_headers(user_a.id)
    headers_b = _get_auth_headers(user_b.id)

    # User A creates a document
    create_resp = client.post(
        "/api/v1/documents",
        json={"type": "employment", "details": {"employeeName": "John Doe"}},
        headers=headers_a,
    )
    assert create_resp.status_code == 201
    doc_id = create_resp.json()["document_id"]

    # User A can list and retrieve it
    list_a = client.get("/api/v1/documents", headers=headers_a)
    assert list_a.status_code == 200
    assert any(doc["document_id"] == doc_id for doc in list_a.json())

    get_a = client.get(f"/api/v1/documents/{doc_id}", headers=headers_a)
    assert get_a.status_code == 200
    assert get_a.json()["document_id"] == doc_id

    # User B list does NOT contain User A's document
    list_b = client.get("/api/v1/documents", headers=headers_b)
    assert list_b.status_code == 200
    assert not any(doc["document_id"] == doc_id for doc in list_b.json())

    # User B gets 404 when attempting direct access to User A's document
    get_b = client.get(f"/api/v1/documents/{doc_id}", headers=headers_b)
    assert get_b.status_code == 404
    assert get_b.json()["detail"] == "Document not found."


def test_cross_user_assistant_conversation_isolation(
    client: TestClient, db: Session
) -> None:
    """User A creates a conversation; User B cannot read or send messages to it."""
    user_a = _create_user(db, "usera.chat@example.com", "User A")
    user_b = _create_user(db, "userb.chat@example.com", "User B")
    headers_a = _get_auth_headers(user_a.id)
    headers_b = _get_auth_headers(user_b.id)

    # User A starts a conversation
    msg_a = client.post(
        "/api/v1/assistant/messages",
        json={"message": "Confidential legal query from User A"},
        headers=headers_a,
    )
    assert msg_a.status_code == 200
    conv_id = msg_a.json()["conversation_id"]

    # User A can read own conversation
    read_a = client.get(
        f"/api/v1/assistant/conversations/{conv_id}", headers=headers_a
    )
    assert read_a.status_code == 200
    assert read_a.json()["conversation_id"] == conv_id

    # User B gets 404 when reading User A's conversation
    read_b = client.get(
        f"/api/v1/assistant/conversations/{conv_id}", headers=headers_b
    )
    assert read_b.status_code == 404
    assert read_b.json()["detail"] == "Conversation not found."

    # User B gets 404 when trying to append a message to User A's conversation
    msg_b = client.post(
        "/api/v1/assistant/messages",
        json={
            "conversation_id": conv_id,
            "message": "User B trying to inject into User A conversation",
        },
        headers=headers_b,
    )
    assert msg_b.status_code == 404
    assert msg_b.json()["detail"] == "Conversation not found."


def test_cross_user_history_isolation(client: TestClient, db: Session) -> None:
    """User A's history items are not visible or accessible to User B."""
    user_a = _create_user(db, "usera.hist@example.com", "User A")
    user_b = _create_user(db, "userb.hist@example.com", "User B")
    headers_a = _get_auth_headers(user_a.id)
    headers_b = _get_auth_headers(user_b.id)

    # Add history item for User A
    item_a = HistoryItem(
        id="history-item-usera",
        item_type="document",
        title="User A NDAs",
        description="NDA drafted",
        category="Contracts",
        status="Completed",
        updated_at="Just now",
        related_route="/app/documents/nda-1",
        user_id=user_a.id,
        prototype=True,
    )
    db.add(item_a)
    db.commit()

    # User A sees item
    list_a = client.get("/api/v1/history", headers=headers_a)
    assert list_a.status_code == 200
    assert any(i["item_id"] == "history-item-usera" for i in list_a.json()["items"])

    get_a = client.get(
        "/api/v1/history/history-item-usera", headers=headers_a
    )
    assert get_a.status_code == 200

    # User B list does not contain User A's item
    list_b = client.get("/api/v1/history", headers=headers_b)
    assert list_b.status_code == 200
    assert not any(
        i["item_id"] == "history-item-usera" for i in list_b.json()["items"]
    )

    # User B gets 404 on direct item request
    get_b = client.get(
        "/api/v1/history/history-item-usera", headers=headers_b
    )
    assert get_b.status_code == 404
    assert get_b.json()["detail"] == "History item not found."


# ---------------------------------------------------------------------------
# Legacy NULL-Owned Data Policy Tests
# ---------------------------------------------------------------------------


def test_legacy_null_prototype_records_excluded(
    client: TestClient, db: Session
) -> None:
    """Authenticated users never see legacy seed records with user_id = NULL."""
    user = _create_user(db, "user.legacy@example.com", "Legacy Test User")
    headers = _get_auth_headers(user.id)

    # Documents list is empty for new user despite seeded rental-agreement-demo
    docs_resp = client.get("/api/v1/documents", headers=headers)
    assert docs_resp.status_code == 200
    assert len(docs_resp.json()) == 0

    # Reading legacy document returns 404
    doc_detail = client.get(
        "/api/v1/documents/rental-agreement-demo", headers=headers
    )
    assert doc_detail.status_code == 404

    # Reading legacy conversation returns 404
    conv_detail = client.get(
        "/api/v1/assistant/conversations/conversation-demo", headers=headers
    )
    assert conv_detail.status_code == 404

    # Reading legacy history item returns 404
    hist_detail = client.get(
        "/api/v1/history/history-rental-deposit-session", headers=headers
    )
    assert hist_detail.status_code == 404

    # Legacy seed records still exist in database with user_id = NULL
    legacy_doc = db.get(Document, "rental-agreement-demo")
    assert legacy_doc is not None
    assert legacy_doc.user_id is None

    legacy_conv = db.get(AssistantConversation, "conversation-demo")
    assert legacy_conv is not None
    assert legacy_conv.user_id is None


# ---------------------------------------------------------------------------
# Unauthenticated Access Tests
# ---------------------------------------------------------------------------


def test_unauthenticated_requests_receive_401(client: TestClient) -> None:
    """All user-scoped endpoints require valid Bearer authentication."""
    assert client.get("/api/v1/documents").status_code == 401
    assert client.get("/api/v1/documents/some-id").status_code == 401
    assert (
        client.post(
            "/api/v1/documents",
            json={"type": "will", "details": {}},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/assistant/messages", json={"message": "hello"}
        ).status_code
        == 401
    )
    assert (
        client.get("/api/v1/assistant/conversations/some-id").status_code == 401
    )
    assert client.get("/api/v1/history").status_code == 401
    assert client.get("/api/v1/history/some-id").status_code == 401


# ---------------------------------------------------------------------------
# Research Global / Shared Access Tests
# ---------------------------------------------------------------------------


def test_research_remains_global_and_unscoped(
    client: TestClient, db: Session
) -> None:
    """Research search and detail endpoints remain global and open without auth."""
    # Unauthenticated search works
    search_resp = client.post(
        "/api/v1/research/search", json={"query": "property"}
    )
    assert search_resp.status_code == 200
    assert len(search_resp.json()["results"]) >= 1

    # Unauthenticated detail works
    detail_resp = client.get("/api/v1/research/rental-deposit-dispute")
    assert detail_resp.status_code == 200
    assert (
        detail_resp.json()["result_id"] == "rental-deposit-dispute"
    )

    # ResearchRecord model has no user_id column
    assert not hasattr(ResearchRecord, "user_id")
