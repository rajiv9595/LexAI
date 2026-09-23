"""Comprehensive authentication and user security tests."""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.documents import Document
from app.models.history import HistoryItem
from app.models.research import ResearchRecord
from app.models.user import User
from app.repositories import user_repository


# ---------------------------------------------------------------------------
# Registration Tests
# ---------------------------------------------------------------------------


def test_valid_registration(client: TestClient) -> None:
    """1. Valid registration creates user and returns safe representation."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "lawyer.test@example.com",
            "password": "SecurePassword123!",
            "display_name": "Jane Lawyer",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "lawyer.test@example.com"
    assert data["display_name"] == "Jane Lawyer"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_duplicate_email_registration_fails(client: TestClient) -> None:
    """2. Duplicate email returns 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "SecurePassword123!",
        "display_name": "Original User",
    }
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"].lower()


def test_email_normalization(client: TestClient) -> None:
    """3. Email is normalized to lowercase on registration and login."""
    register_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "  USER.CASE@Example.COM  ",
            "password": "SecurePassword123!",
            "display_name": "Case Sensitive User",
        },
    )
    assert register_resp.status_code == 201
    assert register_resp.json()["email"] == "user.case@example.com"

    # Login using different casing
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "User.Case@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_invalid_email_format_fails(client: TestClient) -> None:
    """4. Invalid email format is rejected with 422."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "SecurePassword123!",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 422


def test_weak_short_password_fails(client: TestClient) -> None:
    """5. Password shorter than 8 characters is rejected with 422."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "shortpw@example.com",
            "password": "short",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 422


def test_blank_display_name_fails(client: TestClient) -> None:
    """6. Blank display name is rejected with 422."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "blankname@example.com",
            "password": "SecurePassword123!",
            "display_name": "",
        },
    )
    assert response.status_code == 422


def test_whitespace_only_display_name_fails(client: TestClient) -> None:
    """7. Whitespace-only display name is rejected with 422."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "spacesname@example.com",
            "password": "SecurePassword123!",
            "display_name": "   ",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login Tests
# ---------------------------------------------------------------------------


def test_valid_login(client: TestClient) -> None:
    """8. Valid login returns bearer access token."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login.test@example.com",
            "password": "CorrectPassword123!",
            "display_name": "Login User",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login.test@example.com",
            "password": "CorrectPassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "password" not in data
    assert "password_hash" not in data


def test_login_wrong_password_fails(client: TestClient) -> None:
    """9. Wrong password returns generic 401 Unauthorized."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpw.test@example.com",
            "password": "CorrectPassword123!",
            "display_name": "User",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpw.test@example.com",
            "password": "WrongPassword999!",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_nonexistent_email_fails(client: TestClient) -> None:
    """10. Nonexistent email returns generic 401 (preventing email enumeration)."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "AnyPassword123!",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_inactive_user_fails(client: TestClient, db: Session) -> None:
    """11. Inactive user is rejected on login."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "inactive@example.com",
            "password": "SecurePassword123!",
            "display_name": "Inactive User",
        },
    )
    user = user_repository.get_by_email(db, "inactive@example.com")
    assert user is not None
    user.is_active = False
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# JWT Validation Tests
# ---------------------------------------------------------------------------


def test_valid_jwt_creation_and_decode() -> None:
    """12. Valid JWT creates and decodes subject."""
    token = create_access_token(subject="user-123456")
    subject = decode_access_token(token)
    assert subject == "user-123456"


def test_invalid_jwt_signature_rejected() -> None:
    """13. Token signed with wrong secret is rejected."""
    wrong_token = jwt.encode(
        {"sub": "user-123", "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
        "WRONG_SECRET_KEY_THAT_IS_LONG_ENOUGH_FOR_HMAC_SHA256",
        algorithm="HS256",
    )
    with pytest.raises(ValueError, match="Token is invalid."):
        decode_access_token(wrong_token)


def test_expired_jwt_rejected() -> None:
    """14. Expired token is rejected."""
    expired_token = jwt.encode(
        {"sub": "user-123", "exp": datetime.now(timezone.utc) - timedelta(minutes=10)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(ValueError, match="Token has expired."):
        decode_access_token(expired_token)


def test_malformed_jwt_rejected() -> None:
    """15. Malformed string is rejected."""
    with pytest.raises(ValueError, match="Token is invalid."):
        decode_access_token("this.is.not.a.valid.jwt")


def test_missing_sub_claim_rejected() -> None:
    """16. Token without subject claim is rejected."""
    no_sub_token = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(ValueError, match="Token is invalid."):
        decode_access_token(no_sub_token)


# ---------------------------------------------------------------------------
# /me Authenticated Endpoint Tests
# ---------------------------------------------------------------------------


def test_me_valid_authenticated_request(client: TestClient) -> None:
    """17. Authenticated request with valid bearer token returns user profile."""
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "me.test@example.com",
            "password": "SecurePassword123!",
            "display_name": "Me User",
        },
    )
    user_id = reg.json()["id"]

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "me.test@example.com",
            "password": "SecurePassword123!",
        },
    )
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "me.test@example.com"
    assert data["display_name"] == "Me User"
    assert data["is_active"] is True
    assert "password_hash" not in data


def test_me_missing_authorization_header(client: TestClient) -> None:
    """18. Missing Authorization header returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "required" in response.json()["detail"].lower()


def test_me_malformed_authorization_header(client: TestClient) -> None:
    """19. Malformed header (e.g. missing 'Bearer ') returns 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Basic some_token_string"},
    )
    assert response.status_code == 401
    assert "expected 'bearer" in response.json()["detail"].lower()


def test_me_invalid_bearer_token(client: TestClient) -> None:
    """20. Invalid bearer token returns 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response.status_code == 401


def test_me_expired_bearer_token(client: TestClient) -> None:
    """21. Expired bearer token returns 401."""
    expired_token = jwt.encode(
        {"sub": "some-user-id", "exp": datetime.now(timezone.utc) - timedelta(minutes=5)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_me_nonexistent_user(client: TestClient) -> None:
    """22. Token with subject not present in database returns 401."""
    token = create_access_token(subject="user-nonexistent999")
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "user not found" in response.json()["detail"].lower()


def test_me_inactive_user(client: TestClient, db: Session) -> None:
    """23. Token for deactivated user returns 401."""
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "deactivated@example.com",
            "password": "SecurePassword123!",
            "display_name": "Deactivated User",
        },
    )
    user_id = reg.json()["id"]
    token = create_access_token(subject=user_id)

    user = db.get(User, user_id)
    assert user is not None
    user.is_active = False
    db.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Password Security Tests
# ---------------------------------------------------------------------------


def test_stored_password_is_argon2_hash(db: Session, client: TestClient) -> None:
    """24. Stored password is an Argon2 hash, not plaintext."""
    plaintext = "SuperSecretPassword123!"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "security.check@example.com",
            "password": plaintext,
            "display_name": "Security Check",
        },
    )
    user_id = reg.json()["id"]
    user = db.get(User, user_id)
    assert user is not None
    assert user.password_hash != plaintext
    assert user.password_hash.startswith("$argon2")
    assert verify_password(plaintext, user.password_hash) is True


def test_password_hash_never_exposed_in_schemas(client: TestClient) -> None:
    """25. password_hash is never exposed in register, login, or /me responses."""
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "no.leak@example.com",
            "password": "SecurePassword123!",
            "display_name": "No Leak",
        },
    )
    assert "password_hash" not in reg.json()
    assert "password" not in reg.json()

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "no.leak@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert "password_hash" not in login.json()
    assert "password" not in login.json()

    token = login.json()["access_token"]
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert "password_hash" not in me.json()
    assert "password" not in me.json()


# ---------------------------------------------------------------------------
# Database & Model Tests
# ---------------------------------------------------------------------------


def test_user_persistence_and_lookup(db: Session) -> None:
    """26. User repository creates and retrieves user."""
    pw_hash = hash_password("Password123!")
    user = user_repository.create(
        db=db,
        email="repo.test@example.com",
        password_hash=pw_hash,
        display_name="Repo User",
    )
    db.commit()

    fetched = user_repository.get_by_id(db, user.id)
    assert fetched is not None
    assert fetched.email == "repo.test@example.com"
    assert fetched.display_name == "Repo User"


def test_db_email_uniqueness_enforced(db: Session) -> None:
    """27. Database level unique constraint enforces single email."""
    pw_hash = hash_password("Password123!")
    user_repository.create(
        db=db,
        email="unique@example.com",
        password_hash=pw_hash,
        display_name="First",
    )
    db.commit()

    with pytest.raises(IntegrityError):
        user_repository.create(
            db=db,
            email="unique@example.com",
            password_hash=pw_hash,
            display_name="Second",
        )


def test_prototype_records_intact_and_null_user_id(db: Session) -> None:
    """28 & 30. Seeded prototype records exist and have user_id IS NULL."""
    # Documents
    documents = db.query(Document).all()
    assert len(documents) >= 1
    for doc in documents:
        assert doc.user_id is None
        assert doc.prototype is True

    # Assistant Conversations
    conversations = db.query(AssistantConversation).all()
    assert len(conversations) >= 1
    for conv in conversations:
        assert conv.user_id is None
        assert conv.prototype is True

    # Assistant Messages (linked to conversation, no direct user_id)
    messages = db.query(AssistantMessage).all()
    assert len(messages) >= 1
    for msg in messages:
        assert msg.prototype is True
        assert not hasattr(msg, "user_id")

    # Research records (global, no user_id)
    research = db.query(ResearchRecord).all()
    assert len(research) >= 1
    for item in research:
        assert item.prototype is True
        assert not hasattr(item, "user_id")

    # History items
    history = db.query(HistoryItem).all()
    assert len(history) >= 1
    for item in history:
        assert item.user_id is None
        assert item.prototype is True


def test_public_endpoints_remain_accessible_without_auth(client: TestClient) -> None:
    """29. Public endpoints remain functional without auth headers."""
    # Health
    assert client.get("/api/v1/health").status_code == 200
    # Root
    assert client.get("/").status_code == 200
    # Templates (catalog is public)
    assert client.get("/api/v1/documents/templates").status_code == 200
    # Research search (global/shared)
    assert client.post("/api/v1/research/search", json={"query": "property"}).status_code == 200
