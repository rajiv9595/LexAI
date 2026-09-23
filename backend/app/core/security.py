"""Password hashing (Argon2 via pwdlib) and JWT helpers."""

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

_password_hasher = PasswordHash.recommended()


def hash_password(plaintext_password: str) -> str:
    """Return the Argon2 hash of a plaintext password. Never log the input."""
    return _password_hasher.hash(plaintext_password)


def verify_password(plaintext_password: str, password_hash: str) -> bool:
    """Return True when the plaintext password matches the stored hash."""
    return _password_hasher.verify(plaintext_password, password_hash)


def create_access_token(subject: str) -> str:
    """Create a signed JWT whose subject is the user id."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Validate a JWT and return its subject (user id).

    Raises ValueError for expired, malformed, badly signed, or subject-less
    tokens. Never logs the token.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError("Token is invalid.") from exc
    subject = payload.get("sub")
    if not subject or not isinstance(subject, str):
        raise ValueError("Token is invalid.")
    return subject
