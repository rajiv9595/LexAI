"""User data access through SQLAlchemy sessions."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


def normalize_email(email: str) -> str:
    """Normalize an email address for lookup and persistence."""
    return email.strip().lower()


def get_by_id(db: Session, user_id: str) -> User | None:
    """Return a user by id, if it exists."""
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    """Return a user by normalized email, if one exists."""
    return db.query(User).filter(User.email == normalize_email(email)).first()


def email_exists(db: Session, email: str) -> bool:
    """Return True when the normalized email is already registered."""
    return get_by_email(db, email) is not None


def create(
    db: Session, email: str, password_hash: str, display_name: str
) -> User:
    """Stage a new active user in the transaction. Caller commits."""
    user = User(
        id=f"user-{uuid.uuid4().hex[:12]}",
        email=normalize_email(email),
        password_hash=password_hash,
        display_name=display_name.strip(),
        is_active=True,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise
    return user
