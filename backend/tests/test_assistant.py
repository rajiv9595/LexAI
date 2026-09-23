"""Assistant endpoint tests with user scoping and authentication."""

from fastapi.testclient import TestClient


def test_unauthenticated_post_message_fails(client: TestClient) -> None:
    response = client.post(
        "/api/v1/assistant/messages",
        json={"message": "Should fail unauthenticated"},
    )
    assert response.status_code == 401


def test_post_message_returns_prototype_reply(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/v1/assistant/messages",
        json={"message": "What should I check before signing a contract?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "assistant"
    assert body["prototype"] is True
    assert body["conversation_id"]
    assert body["message_id"]
    assert "prototype" in body["content"].lower()


def test_post_message_rejects_empty_message(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/v1/assistant/messages", json={"message": "   "}
    )
    assert response.status_code == 422


def test_read_conversation_returns_prototype(auth_client: TestClient) -> None:
    # Post a message to create a user-owned conversation
    posted = auth_client.post(
        "/api/v1/assistant/messages",
        json={"message": "Hello assistant"},
    )
    conv_id = posted.json()["conversation_id"]

    response = auth_client.get(f"/api/v1/assistant/conversations/{conv_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"] == conv_id
    assert body["prototype"] is True
    assert len(body["messages"]) == 2


def test_read_conversation_unknown_id_returns_404(
    auth_client: TestClient,
) -> None:
    response = auth_client.get("/api/v1/assistant/conversations/does-not-exist")
    assert response.status_code == 404


def test_legacy_null_conversation_returns_404(auth_client: TestClient) -> None:
    # conversation-demo has user_id = NULL in seed data
    response = auth_client.get(
        "/api/v1/assistant/conversations/conversation-demo"
    )
    assert response.status_code == 404
