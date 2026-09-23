"""Research endpoint tests. Local prototype records only."""

from fastapi.testclient import TestClient


def test_search_returns_matching_prototype_records(client: TestClient) -> None:
    response = client.post(
        "/api/v1/research/search", json={"query": "security deposit dispute"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["prototype"] is True
    assert body["count"] >= 1
    assert all(item["prototype"] is True for item in body["results"])


def test_search_filters_by_source_type(client: TestClient) -> None:
    response = client.post(
        "/api/v1/research/search",
        json={"query": "", "source_type": "statute"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 1
    assert all(item["source_type"] == "statute" for item in body["results"])


def test_search_no_match_returns_empty_list(client: TestClient) -> None:
    response = client.post(
        "/api/v1/research/search", json={"query": "zzzqqq nonexistent topic"}
    )
    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_read_result_valid(client: TestClient) -> None:
    response = client.get("/api/v1/research/rental-deposit-dispute")
    assert response.status_code == 200
    body = response.json()
    assert body["result_id"] == "rental-deposit-dispute"
    assert body["prototype"] is True


def test_read_result_invalid_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/research/unknown-record")
    assert response.status_code == 404
