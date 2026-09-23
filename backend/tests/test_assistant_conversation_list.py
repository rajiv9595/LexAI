"""STEP 24: Authorized assistant conversation list & history UX.

Covers the lightweight discovery endpoint
``GET /api/v1/assistant/conversations``: ownership isolation, legacy
NULL-owned exclusion, sorting, previews, truncation, pagination, and
the guarantee that no reference provenance leaks into list items.
The detail endpoint behavior from STEP 23 is re-verified, not changed.

All AI behavior is faked or bypassed (direct repository writes);
no test reaches the real Gemini API and no external calls are made.
"""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.user import User
from app.repositories import assistant_repository, user_repository
from app.schemas.assistant import ValidatedAssistantReference


def _utc(year: int, month: int, day: int, hour: int = 0) -> datetime:
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


def _make_conv(db, user_id: str | None, conv_id: str, updated: datetime,
               messages: list[tuple[str, str]]) -> None:
    """Create a conversation with explicit ids/timestamps for determinism."""
    db.add(AssistantConversation(
        id=conv_id, user_id=user_id, prototype=True, updated_at=updated))
    for i, (role, content) in enumerate(messages, start=1):
        db.add(AssistantMessage(
            id=f"{conv_id}-message-{i}",
            conversation_id=conv_id,
            role=role,
            content=content,
            prototype=True,
        ))
    db.flush()
    # save_message() bumps updated_at via func.now(); direct writes set it
    # explicitly so sort-order tests are deterministic.
    db.query(AssistantConversation).filter(
        AssistantConversation.id == conv_id
    ).update(
        {AssistantConversation.updated_at: updated},
        synchronize_session=False,
    )
    db.commit()


def _other_client(client: TestClient, db, email: str) -> TestClient:
    other = user_repository.create(
        db=db,
        email=email,
        password_hash=hash_password("Password123!"),
        display_name="Other User",
    )
    db.commit()
    client.headers["Authorization"] = (
        f"Bearer {create_access_token(subject=other.id)}"
    )
    return client


def _list(auth_client: TestClient, query: str = ""):
    return auth_client.get(f"/api/v1/assistant/conversations{query}")


def test_list_returns_only_own_conversations(
    auth_client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, test_user.id, "conv-mine", _utc(2026, 9, 20),
               [("user", "My landlord kept my deposit.")])
    response = _list(auth_client)
    assert response.status_code == 200
    body = response.json()
    ids = [item["conversation_id"] for item in body["items"]]
    assert "conv-mine" in ids
    # Legacy NULL-owned seed conversation is never listed.
    assert "conversation-demo" not in ids


def test_null_owned_conversations_excluded(
    auth_client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, None, "conv-null", _utc(2026, 9, 21),
               [("user", "Orphaned legacy message.")])
    ids = [item["conversation_id"] for item in _list(auth_client).json()["items"]]
    assert "conv-null" not in ids


def test_user_a_cannot_see_user_b_conversations(
    auth_client: TestClient, client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, test_user.id, "conv-a-private", _utc(2026, 9, 20),
               [("user", "Private question.")])
    other_client = _other_client(client, db, "other.list@example.com")
    body = other_client.get("/api/v1/assistant/conversations").json()
    assert body["total"] == 0
    assert body["items"] == []
    assert "conv-a-private" not in [
        item["conversation_id"] for item in body["items"]]


def test_unauthenticated_request_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/assistant/conversations")
    assert response.status_code == 401


def test_empty_user_returns_empty_list(
    client: TestClient, db
) -> None:
    empty_client = _other_client(client, db, "empty.list@example.com")
    response = empty_client.get("/api/v1/assistant/conversations")
    assert response.status_code == 200
    assert response.json() == {
        "items": [], "page": 1, "page_size": 20, "total": 0}


def test_sorted_newest_updated_first(
    auth_client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, test_user.id, "conv-old", _utc(2026, 9, 18),
               [("user", "Old question.")])
    _make_conv(db, test_user.id, "conv-new", _utc(2026, 9, 22),
               [("user", "New question.")])
    _make_conv(db, test_user.id, "conv-mid", _utc(2026, 9, 20),
               [("user", "Mid question.")])
    ids = [item["conversation_id"]
           for item in _list(auth_client).json()["items"]]
    assert ids == ["conv-new", "conv-mid", "conv-old"]


def test_tie_break_conversation_id_desc(
    auth_client: TestClient, db, test_user: User
) -> None:
    same = _utc(2026, 9, 20, hour=12)
    _make_conv(db, test_user.id, "conv-tie-a", same, [("user", "A.")])
    _make_conv(db, test_user.id, "conv-tie-b", same, [("user", "B.")])
    ids = [item["conversation_id"]
           for item in _list(auth_client).json()["items"]]
    assert ids.index("conv-tie-b") < ids.index("conv-tie-a")


def test_message_count(
    auth_client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, test_user.id, "conv-count", _utc(2026, 9, 20), [
        ("user", "First."), ("assistant", "Reply."), ("user", "Follow-up.")])
    _make_conv(db, test_user.id, "conv-empty", _utc(2026, 9, 19), [])
    by_id = {item["conversation_id"]: item
             for item in _list(auth_client).json()["items"]}
    assert by_id["conv-count"]["message_count"] == 3
    assert by_id["conv-empty"]["message_count"] == 0


def test_earliest_user_message_preview(
    auth_client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, test_user.id, "conv-preview", _utc(2026, 9, 20), [
        ("assistant", "Welcome, how can I help?"),
        ("user", "First user question about deposits."),
        ("assistant", "An answer."),
        ("user", "Second user question."),
    ])
    by_id = {item["conversation_id"]: item
             for item in _list(auth_client).json()["items"]}
    assert (by_id["conv-preview"]["first_user_message_preview"]
            == "First user question about deposits.")


def test_assistant_only_conversation_has_null_preview(
    auth_client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, test_user.id, "conv-no-user", _utc(2026, 9, 20),
               [("assistant", "System-style reply with no user prompt.")])
    by_id = {item["conversation_id"]: item
             for item in _list(auth_client).json()["items"]}
    assert by_id["conv-no-user"]["first_user_message_preview"] is None


def test_preview_truncation_is_deterministic(
    auth_client: TestClient, db, test_user: User
) -> None:
    long_message = "x" * 300
    _make_conv(db, test_user.id, "conv-long", _utc(2026, 9, 20),
               [("user", long_message)])
    by_id = {item["conversation_id"]: item
             for item in _list(auth_client).json()["items"]}
    preview = by_id["conv-long"]["first_user_message_preview"]
    assert preview == "x" * 160 + "\u2026"
    assert len(preview) == 161


def test_pagination_page_one_and_two(
    auth_client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, test_user.id, "conv-p1", _utc(2026, 9, 18), [("user", "One.")])
    _make_conv(db, test_user.id, "conv-p2", _utc(2026, 9, 19), [("user", "Two.")])
    _make_conv(db, test_user.id, "conv-p3", _utc(2026, 9, 20), [("user", "Three.")])
    page1 = _list(auth_client, "?page=1&page_size=2").json()
    assert (page1["page"], page1["page_size"], page1["total"]) == (1, 2, 3)
    assert [i["conversation_id"] for i in page1["items"]] == ["conv-p3", "conv-p2"]
    page2 = _list(auth_client, "?page=2&page_size=2").json()
    assert (page2["page"], page2["page_size"], page2["total"]) == (2, 2, 3)
    assert [i["conversation_id"] for i in page2["items"]] == ["conv-p1"]


def test_pagination_limits_enforced(auth_client: TestClient) -> None:
    assert _list(auth_client, "?page=0").status_code == 422
    assert _list(auth_client, "?page_size=0").status_code == 422
    assert _list(auth_client, "?page_size=101").status_code == 422


def test_total_count_is_correct(
    auth_client: TestClient, db, test_user: User
) -> None:
    for day in (18, 19, 20, 21):
        _make_conv(db, test_user.id, f"conv-total-{day}", _utc(2026, 9, day),
                   [("user", f"Question {day}.")])
    body = _list(auth_client, "?page=1&page_size=2").json()
    assert body["total"] == 4


def test_no_references_in_list_response(
    auth_client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, test_user.id, "conv-noref", _utc(2026, 9, 20),
               [("user", "Deposit question."), ("assistant", "Answer.")])
    assistant_repository.save_message_references(
        db, "conv-noref-message-2",
        [ValidatedAssistantReference(
            source_id="rental-deposit-dispute",
            title="Rental Deposit Dispute \u2014 Prototype Research Record",
            citation_label="Demo case record",
            source_type="case",
            jurisdiction="Prototype / General",
            prototype=True,
        )],
    )
    db.commit()
    item = _list(auth_client).json()["items"][0]
    assert set(item.keys()) == {
        "conversation_id", "updated_at", "message_count",
        "first_user_message_preview",
    }


def test_detail_still_returns_persisted_references(
    auth_client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, test_user.id, "conv-detail", _utc(2026, 9, 20),
               [("user", "Deposit question."), ("assistant", "Answer.")])
    assistant_repository.save_message_references(
        db, "conv-detail-message-2",
        [ValidatedAssistantReference(
            source_id="rental-deposit-dispute",
            title="Rental Deposit Dispute \u2014 Prototype Research Record",
            citation_label="Demo case record",
            source_type="case",
            jurisdiction="Prototype / General",
            prototype=True,
        )],
    )
    db.commit()
    detail = auth_client.get(
        "/api/v1/assistant/conversations/conv-detail").json()
    refs = [m for m in detail["messages"] if m["role"] == "assistant"][0][
        "references"]
    assert [r["source_id"] for r in refs] == ["rental-deposit-dispute"]
    assert refs[0]["title"].startswith("Rental Deposit Dispute")


def test_cross_user_detail_remains_protected(
    auth_client: TestClient, client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, test_user.id, "conv-secret", _utc(2026, 9, 20),
               [("user", "Secret question.")])
    other_client = _other_client(client, db, "snoop.list@example.com")
    assert other_client.get(
        "/api/v1/assistant/conversations/conv-secret").status_code == 404
    # NOTE: auth_client wraps the same TestClient as client, so restore
    # the owner's token before reading back as the owner.
    client.headers["Authorization"] = (
        f"Bearer {create_access_token(subject=test_user.id)}"
    )
    # Owner access unaffected.
    assert auth_client.get(
        "/api/v1/assistant/conversations/conv-secret").status_code == 200


def test_new_message_bumps_conversation_updated_at(
    auth_client: TestClient, db, test_user: User
) -> None:
    _make_conv(db, test_user.id, "conv-bump-old", _utc(2026, 9, 10),
               [("user", "Stale question.")])
    posted = auth_client.post(
        "/api/v1/assistant/messages", json={"message": "Fresh question"})
    assert posted.status_code == 200
    ids = [item["conversation_id"]
           for item in _list(auth_client).json()["items"]]
    assert ids[0] == posted.json()["conversation_id"]
