"""Assistant rate-limit handling: provider 429 -> HTTP 429 with safe code.

All provider behavior is faked; no test reaches the real Gemini API.
"""

from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from app.ai.providers.gemini import (
    GeminiAuthenticationError,
    GeminiRateLimitError,
    GeminiResponseError,
)
from app.services import assistant_service


def _enable_ai(monkeypatch: pytest.MonkeyPatch, orchestrator_cls: type) -> None:
    """Opt into the AI path with a stubbed orchestrator (never real Gemini)."""
    monkeypatch.setattr(assistant_service.settings, "ai_enabled", True)
    monkeypatch.setattr(
        assistant_service, "AssistantOrchestrator", orchestrator_cls
    )


class _RateLimitedOrchestrator:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def process_query(self, **kwargs):
        raise GeminiRateLimitError(
            "RESOURCE_EXHAUSTED: quota exceeded for test"
        )


class _BrokenOrchestrator:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def process_query(self, **kwargs):
        raise GeminiResponseError("malformed test response")


class _AuthFailedOrchestrator:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def process_query(self, **kwargs):
        raise GeminiAuthenticationError("invalid test key")


class _WorkingOrchestrator:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def process_query(self, **kwargs):
        return SimpleNamespace(answer="AI answer for test")


def test_rate_limit_maps_to_429_with_safe_code(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_ai(monkeypatch, _RateLimitedOrchestrator)
    response = auth_client.post(
        "/api/v1/assistant/messages", json={"message": "Hello"}
    )
    assert response.status_code == 429
    body = response.json()
    assert body["detail"]["code"] == "AI_PROVIDER_RATE_LIMITED"
    assert "usage limit" in body["detail"]["message"]
    text = response.text
    assert "RESOURCE_EXHAUSTED" not in text
    assert "Traceback" not in text
    assert "GEMINI_API_KEY" not in text
    assert "AIza" not in text


def test_non429_provider_error_stays_502(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_ai(monkeypatch, _BrokenOrchestrator)
    response = auth_client.post(
        "/api/v1/assistant/messages", json={"message": "Hello"}
    )
    assert response.status_code == 502


def test_auth_failure_is_not_mapped_to_429(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_ai(monkeypatch, _AuthFailedOrchestrator)
    response = auth_client.post(
        "/api/v1/assistant/messages", json={"message": "Hello"}
    )
    assert response.status_code == 502


def test_success_path_unchanged(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_ai(monkeypatch, _WorkingOrchestrator)
    response = auth_client.post(
        "/api/v1/assistant/messages", json={"message": "Hello"}
    )
    assert response.status_code == 200
    assert response.json()["content"] == "AI answer for test"
