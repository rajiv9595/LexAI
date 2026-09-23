"""History endpoint tests with user scoping and authentication."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.history import HistoryItem


def test_unauthenticated_history_list_fails(client: TestClient) -> None:
    response = client.get("/api/v1/history")
    assert response.status_code == 401


def test_list_history_returns_user_items_only(
    auth_client: TestClient, db: Session, test_user
) -> None:
    # Initially user has no history
    response = auth_client.get("/api/v1/history")
    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert len(response.json()["items"]) == 0

    # Add a history item owned by this user
    item = HistoryItem(
        id="user-history-item-1",
        item_type="document",
        title="User Contract",
        description="Drafted contract",
        category="Contracts",
        status="Draft",
        updated_at="Just now",
        related_route="/app/documents/1",
        user_id=test_user.id,
        prototype=True,
    )
    db.add(item)
    db.commit()

    response = auth_client.get("/api/v1/history")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["item_id"] == "user-history-item-1"


def test_read_history_item_valid(
    auth_client: TestClient, db: Session, test_user
) -> None:
    item = HistoryItem(
        id="user-history-item-2",
        item_type="assistant",
        title="Chat session",
        description="Consultation",
        category="Advisory",
        status="Completed",
        updated_at="Today",
        related_route="/app/assistant",
        user_id=test_user.id,
        prototype=True,
    )
    db.add(item)
    db.commit()

    response = auth_client.get("/api/v1/history/user-history-item-2")
    assert response.status_code == 200
    body = response.json()
    assert body["item_id"] == "user-history-item-2"
    assert body["prototype"] is True


def test_read_history_item_invalid_returns_404(
    auth_client: TestClient,
) -> None:
    response = auth_client.get("/api/v1/history/unknown-item")
    assert response.status_code == 404


def test_legacy_null_history_returns_404(auth_client: TestClient) -> None:
    # Legacy seed items have user_id = NULL
    response = auth_client.get(
        "/api/v1/history/history-rental-deposit-session"
    )
    assert response.status_code == 404
