"""Shared pytest fixtures: SQLite-backed sessions with dependency overrides.

SQLite is used so the suite runs without a live PostgreSQL server.
All ORM constructs used here (String, Boolean, DateTime, JSON, FK,
relationships, check constraints) behave the same on PostgreSQL.
"""

from collections.abc import Iterator
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.data.seed import seed_database
from app.main import app
from app.models.user import User
from app.repositories import user_repository


@pytest.fixture(name="db")
def db_fixture() -> Session:
    """Return a fresh seeded SQLite session backed by a shared connection."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    seed_database(session)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture(name="client")
def client_fixture(db: Session) -> TestClient:
    """Return a test client whose DB dependency uses the fixture session."""

    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(db: Session) -> User:
    """Create a default active test user."""
    user = user_repository.create(
        db=db,
        email="test.default.user@example.com",
        password_hash=hash_password("Password123!"),
        display_name="Default Test User",
    )
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, test_user: User) -> TestClient:
    """Return a TestClient pre-authenticated as test_user."""
    token = create_access_token(subject=test_user.id)
    client.headers["Authorization"] = f"Bearer {token}"
    return client
