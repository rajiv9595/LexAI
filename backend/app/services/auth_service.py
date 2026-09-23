"""Authentication and user management business logic."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


def register_user(db: Session, payload: RegisterRequest) -> User:
    """Register a new user account with hashed password and normalized email.

    Raises 409 Conflict if the email is already registered.
    """
    normalized_email = user_repository.normalize_email(payload.email)
    if user_repository.email_exists(db, normalized_email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    hashed_pw = hash_password(payload.password)
    user = user_repository.create(
        db=db,
        email=normalized_email,
        password_hash=hashed_pw,
        display_name=payload.display_name.strip(),
    )
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: LoginRequest) -> TokenResponse:
    """Validate user credentials and return a bearer access token.

    Returns a generic 401 error for nonexistent users or wrong passwords
    to prevent email enumeration.
    """
    normalized_email = user_repository.normalize_email(payload.email)
    user = user_repository.get_by_email(db, normalized_email)

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.id)
    return TokenResponse(access_token=access_token, token_type="bearer")
