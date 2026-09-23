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
    # Initially user has no documents
    initial = auth_client.get("/api/v1/documents")
    assert initial.status_code == 200
    assert len(initial.json()) == 0

    # User creates a document
    created = auth_client.post(
        "/api/v1/documents",
        json={"type": "rental", "details": {"tenantName": "Alice"}},
    )
    assert created.status_code == 201
    doc_id = created.json()["document_id"]

    # User now sees the document
    response = auth_client.get("/api/v1/documents")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["document_id"] == doc_id


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
    assert body["prototype"] is True


def test_read_document_invalid_returns_404(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/documents/unknown-document")
    assert response.status_code == 404


def test_legacy_null_document_returns_404(auth_client: TestClient) -> None:
    # Legacy prototype record has user_id = NULL
    response = auth_client.get("/api/v1/documents/rental-agreement-demo")
    assert response.status_code == 404


def test_create_document_returns_prototype_draft(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/v1/documents",
        json={"type": "nda", "details": {"disclosingParty": "Example Party A"}},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "nda"
    assert body["status"] == "Prototype Draft"
    assert body["prototype"] is True
    assert body["details"]["disclosingParty"] == "Example Party A"


def test_create_document_rejects_invalid_type(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/api/v1/documents", json={"type": "passport", "details": {}}
    )
    assert response.status_code == 422
