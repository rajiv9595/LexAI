"""STEP 23: Persisted validated references & history provenance.

All provider behavior is faked (scripted mock / stubbed orchestrators);
no test reaches the real Gemini API and no external calls are made.
SQLite is used via the shared fixtures; FK enforcement is enabled locally
only for the RESTRICT test (PostgreSQL enforces it unconditionally).
"""

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.ai.models.responses import AIRequest, AIResponse, SafetyStatus
from app.ai.models.responses import LegalReferenceItem
from app.ai.providers.base import MockDeterministicAIProvider
from app.ai.services.assistant_orchestrator import AssistantOrchestrator
from app.core.security import create_access_token, hash_password
from app.models.assistant import AssistantMessageReference
from app.models.research import ResearchRecord
from app.models.user import User
from app.repositories import assistant_repository, user_repository
from app.schemas.assistant import ValidatedAssistantReference
from app.services import assistant_service


RENTAL_ID = "rental-deposit-dispute"
RENTAL_TITLE = "Rental Deposit Dispute — Prototype Research Record"
RENTAL_CITATION = "Demo case record"
EMPLOY_ID = "employment-termination"
EMPLOY_TITLE = "Employment Termination — Prototype Research Record"
EMPLOY_CITATION = "Prototype reference"


def _enable_ai(monkeypatch: pytest.MonkeyPatch, orchestrator_factory) -> None:
    monkeypatch.setattr(assistant_service.settings, "ai_enabled", True)
    monkeypatch.setattr(
        assistant_service, "AssistantOrchestrator", orchestrator_factory
    )


class _ScriptedMock(MockDeterministicAIProvider):
    """Mock provider returning scripted final-answer JSON (offline)."""

    def __init__(self, final_payload) -> None:
        super().__init__()
        self.final_payload = final_payload

    def generate(self, request: AIRequest) -> AIResponse:
        if request.response_schema_name == "query_understanding":
            return super().generate(request)
        content = (
            self.final_payload
            if isinstance(self.final_payload, str)
            else json.dumps(self.final_payload)
        )
        return AIResponse(
            content=content,
            provider=self.provider_name,
            model="mock-v1",
            safety_status=SafetyStatus.SAFE,
        )


def _real_orchestrator_with(final_payload):
    def _factory(*args, **kwargs):
        return AssistantOrchestrator(provider=_ScriptedMock(final_payload))

    return _factory


def _ref_dto(source_id: str, **overrides) -> ValidatedAssistantReference:
    base = {
        "source_id": source_id,
        "title": f"Title {source_id}",
        "citation_label": f"Citation {source_id}",
        "source_type": "case",
        "jurisdiction": "Prototype / General",
        "prototype": True,
    }
    base.update(overrides)
    return ValidatedAssistantReference(**base)


def _post_deposit_answer(auth_client: TestClient, monkeypatch) -> dict:
    """POST a deposit question whose scripted answer cites 2 records in order."""
    final = {
        "answer": "Deposit guidance grounded in retrieved records.",
        "references": [
            {
                "title": "Tampered",
                "kind": "tampered",
                "source_id": EMPLOY_ID,
                "citation": EMPLOY_CITATION,
            },
            {
                "title": "Tampered",
                "kind": "tampered",
                "source_id": RENTAL_ID,
                "citation": RENTAL_CITATION,
            },
        ],
    }
    _enable_ai(monkeypatch, _real_orchestrator_with(final))
    response = auth_client.post(
        "/api/v1/assistant/messages",
        json={
            "message": "My landlord kept my security deposit. "
            "I also have questions about employment termination procedures."
        },
    )
    assert response.status_code == 200
    return response.json()


def test_round_trip_preserves_metadata_and_order(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch, db
) -> None:
    body = _post_deposit_answer(auth_client, monkeypatch)
    assert [r["source_id"] for r in body["references"]] == [EMPLOY_ID, RENTAL_ID]

    convo = auth_client.get(
        f"/api/v1/assistant/conversations/{body['conversation_id']}"
    )
    assert convo.status_code == 200
    assistant_msgs = [
        m for m in convo.json()["messages"] if m["role"] == "assistant"
    ]
    assert len(assistant_msgs) == 1
    refs = assistant_msgs[0]["references"]
    assert [r["source_id"] for r in refs] == [EMPLOY_ID, RENTAL_ID]
    assert refs[0]["title"] == EMPLOY_TITLE
    assert refs[0]["citation_label"] == EMPLOY_CITATION
    assert refs[0]["source_type"] == "precedent"
    assert refs[1]["title"] == RENTAL_TITLE
    # No internal-only columns leak into the API.
    assert set(refs[0].keys()) == {
        "source_id",
        "title",
        "citation_label",
        "source_type",
        "jurisdiction",
        "prototype",
    }
    rows = (
        db.query(AssistantMessageReference)
        .order_by(AssistantMessageReference.position)
        .all()
    )
    assert [(r.research_record_id, r.position) for r in rows] == [
        (EMPLOY_ID, 0),
        (RENTAL_ID, 1),
    ]


def test_historical_snapshot_survives_record_update(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch, db
) -> None:
    body = _post_deposit_answer(auth_client, monkeypatch)
    record = db.get(ResearchRecord, RENTAL_ID)
    assert record is not None
    record.title = "CHANGED TITLE"
    record.citation_label = "CHANGED CITATION"
    db.commit()

    convo = auth_client.get(
        f"/api/v1/assistant/conversations/{body['conversation_id']}"
    )
    refs = [
        m for m in convo.json()["messages"] if m["role"] == "assistant"
    ][0]["references"]
    rental = next(r for r in refs if r["source_id"] == RENTAL_ID)
    assert rental["title"] == RENTAL_TITLE
    assert rental["citation_label"] == RENTAL_CITATION


def test_old_and_sourceless_messages_return_empty_references(
    auth_client: TestClient, db
) -> None:
    # Prototype mode persists no reference rows at all.
    posted = auth_client.post(
        "/api/v1/assistant/messages", json={"message": "Hello assistant"}
    )
    assert posted.json()["references"] == []
    assert db.query(AssistantMessageReference).count() == 0
    convo = auth_client.get(
        f"/api/v1/assistant/conversations/{posted.json()['conversation_id']}"
    )
    for message in convo.json()["messages"]:
        assert message["references"] == []


def test_user_messages_carry_no_references(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = _post_deposit_answer(auth_client, monkeypatch)
    convo = auth_client.get(
        f"/api/v1/assistant/conversations/{body['conversation_id']}"
    )
    user_msgs = [m for m in convo.json()["messages"] if m["role"] == "user"]
    assert len(user_msgs) == 1
    assert user_msgs[0]["references"] == []


def test_duplicate_input_deduped_deterministically(db, test_user: User) -> None:
    from app.models.assistant import AssistantConversation, AssistantMessage

    db.add(AssistantConversation(id="conv-dup", user_id=test_user.id, prototype=True))
    db.add(
        AssistantMessage(
            id="conv-dup-message-1",
            conversation_id="conv-dup",
            role="assistant",
            content="answer",
            prototype=True,
        )
    )
    db.flush()
    count = assistant_repository.save_message_references(
        db,
        "conv-dup-message-1",
        [_ref_dto(RENTAL_ID), _ref_dto(RENTAL_ID), _ref_dto(EMPLOY_ID)],
    )
    assert count == 2
    rows = (
        db.query(AssistantMessageReference)
        .filter(AssistantMessageReference.message_id == "conv-dup-message-1")
        .order_by(AssistantMessageReference.position)
        .all()
    )
    assert [(r.research_record_id, r.position) for r in rows] == [
        (RENTAL_ID, 0),
        (EMPLOY_ID, 1),
    ]


def test_dangling_reference_fails_safely(db, test_user: User) -> None:
    from app.models.assistant import AssistantConversation, AssistantMessage

    db.add(AssistantConversation(id="conv-bad", user_id=test_user.id, prototype=True))
    db.add(
        AssistantMessage(
            id="conv-bad-message-1",
            conversation_id="conv-bad",
            role="assistant",
            content="answer",
            prototype=True,
        )
    )
    db.flush()
    with pytest.raises(ValueError, match="unknown research records"):
        assistant_repository.save_message_references(
            db, "conv-bad-message-1", [_ref_dto("no-such-record")]
        )


def test_cross_user_isolation(
    auth_client: TestClient, client: TestClient, monkeypatch, db, test_user: User
) -> None:
    body = _post_deposit_answer(auth_client, monkeypatch)
    conv_id = body["conversation_id"]

    other = user_repository.create(
        db=db,
        email="other.user@example.com",
        password_hash=hash_password("Password123!"),
        display_name="Other User",
    )
    db.commit()
    other_token = create_access_token(subject=other.id)
    client.headers["Authorization"] = f"Bearer {other_token}"

    # Conversation, message, and nested references unreachable by ID games.
    # NOTE: auth_client wraps the same TestClient as client, so restore the
    # owner's token before reading back as the owner.
    assert client.get(f"/api/v1/assistant/conversations/{conv_id}").status_code == 404
    # No global reference endpoint exists.
    assert client.get("/api/v1/references/anything").status_code == 404
    client.headers["Authorization"] = f"Bearer {create_access_token(subject=test_user.id)}"
    # Owner still sees persisted references.
    mine = auth_client.get(f"/api/v1/assistant/conversations/{conv_id}")
    assert len(mine.json()["messages"][1]["references"]) == 2


def test_restrict_blocks_referenced_record_delete(db) -> None:
    db.execute(text("PRAGMA foreign_keys=ON"))
    from app.models.assistant import AssistantConversation, AssistantMessage

    db.add(AssistantConversation(id="conv-del", user_id=None, prototype=True))
    db.add(
        AssistantMessage(
            id="conv-del-message-1",
            conversation_id="conv-del",
            role="assistant",
            content="answer",
            prototype=True,
        )
    )
    db.flush()
    assistant_repository.save_message_references(
        db, "conv-del-message-1", [_ref_dto(RENTAL_ID)]
    )
    db.commit()
    with pytest.raises(IntegrityError):
        db.delete(db.get(ResearchRecord, RENTAL_ID))
        db.flush()
    db.rollback()
    # History survives the blocked delete; unreferenced records stay deletable.
    assert (
        db.query(AssistantMessageReference)
        .filter(AssistantMessageReference.message_id == "conv-del-message-1")
        .count()
        == 1
    )
    db.delete(db.get(ResearchRecord, "contract-review-basics"))
    db.commit()
    assert (
        db.query(AssistantMessageReference)
        .filter(AssistantMessageReference.message_id == "conv-del-message-1")
        .count()
        == 1
    )


def test_cascade_removes_refs_with_message(db) -> None:
    db.execute(text("PRAGMA foreign_keys=ON"))
    from app.models.assistant import AssistantConversation, AssistantMessage

    db.add(AssistantConversation(id="conv-cas", user_id=None, prototype=True))
    db.add(
        AssistantMessage(
            id="conv-cas-message-1",
            conversation_id="conv-cas",
            role="assistant",
            content="answer",
            prototype=True,
        )
    )
    db.flush()
    assistant_repository.save_message_references(
        db, "conv-cas-message-1", [_ref_dto(RENTAL_ID)]
    )
    db.delete(db.get(AssistantMessage, "conv-cas-message-1"))
    db.flush()
    assert (
        db.query(AssistantMessageReference)
        .filter(AssistantMessageReference.message_id == "conv-cas-message-1")
        .count()
        == 0
    )


def test_stub_orchestrator_without_refs_persists_nothing(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch, db
) -> None:
    class _AnswerOnly:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def process_query(self, **kwargs):
            return SimpleNamespace(answer="AI answer without references")

    monkeypatch.setattr(assistant_service.settings, "ai_enabled", True)
    monkeypatch.setattr(assistant_service, "AssistantOrchestrator", _AnswerOnly)
    body = auth_client.post(
        "/api/v1/assistant/messages", json={"message": "Hello"}
    ).json()
    assert body["references"] == []
    assert db.query(AssistantMessageReference).count() == 0
