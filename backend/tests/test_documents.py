"""Document endpoint tests with user scoping and authentication."""

from fastapi.testclient import TestClient


def test_unauthenticated_documents_list_fails(client: TestClient) -> None:
    response = client.get("/api/v1/documents")
    assert response.status_code == 401


def test_list_templates_is_public(client: TestClient) -> None:
    response = client.get("/api/v1/documents/templates")
    assert response.status_code == 200
    assert len(response.json()) >= 4


def test_list_documents_returns_user_created_documents(
    auth_client: TestClient,
) -> None:
    initial = auth_client.get("/api/v1/documents")
    assert initial.status_code == 200
    assert len(initial.json()) == 0

    created = auth_client.post(
        "/api/v1/documents",
        json={"type": "rental", "details": {"tenantName": "Alice"}},
    )
    assert created.status_code == 201
    doc_id = created.json()["document_id"]

    response = auth_client.get("/api/v1/documents")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["document_id"] == doc_id
    assert docs[0]["status"] == "Draft"
    assert docs[0]["prototype"] is False
    assert docs[0]["updated_date"]


def test_read_document_valid(auth_client: TestClient) -> None:
    created = auth_client.post(
        "/api/v1/documents",
        json={"type": "nda", "details": {"disclosingParty": "Acme Corp"}},
    )
    doc_id = created.json()["document_id"]

    response = auth_client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == doc_id
    assert body["type"] == "nda"
    assert body["prototype"] is False


def test_read_document_invalid_returns_404(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/documents/unknown-document")
    assert response.status_code == 404


def test_legacy_null_document_returns_404(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/documents/rental-agreement-demo")
    assert response.status_code == 404


def test_create_document_returns_persistent_draft(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/v1/documents",
        json={"type": "nda", "details": {"disclosingParty": "Example Party A"}},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "nda"
    assert body["status"] == "Draft"
    assert body["prototype"] is False
    assert body["details"]["disclosingParty"] == "Example Party A"


def test_update_document_changes_title_and_details(
    auth_client: TestClient,
) -> None:
    created = auth_client.post(
        "/api/v1/documents",
        json={"type": "nda", "details": {"disclosingParty": "Party A"}},
    )
    assert created.status_code == 201
    doc_id = created.json()["document_id"]

    response = auth_client.patch(
        f"/api/v1/documents/{doc_id}",
        json={"title": "Mutual NDA", "details": {"disclosingParty": "Party A", "term": "2 years"}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Mutual NDA"
    assert body["details"]["term"] == "2 years"
    assert body["updated_date"]


def test_update_document_requires_at_least_one_field(
    auth_client: TestClient,
) -> None:
    created = auth_client.post(
        "/api/v1/documents",
        json={"type": "nda", "details": {}},
    )
    doc_id = created.json()["document_id"]

    response = auth_client.patch(f"/api/v1/documents/{doc_id}", json={})
    assert response.status_code == 422


def test_delete_document_removes_owned_document(
    auth_client: TestClient,
) -> None:
    created = auth_client.post(
        "/api/v1/documents",
        json={"type": "will", "details": {"testatorName": "Alice"}},
    )
    doc_id = created.json()["document_id"]

    response = auth_client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 204
    assert auth_client.get(f"/api/v1/documents/{doc_id}").status_code == 404


def test_create_document_rejects_invalid_type(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/v1/documents", json={"type": "passport", "details": {}}
    )
    assert response.status_code == 422
