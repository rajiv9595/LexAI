"""Authentication request/response schemas. Never carries password hashes."""

from pydantic import BaseModel, Field, field_validator


def _validate_email_format(value: str) -> str:
    cleaned = value.strip().lower()
    local, separator, domain = cleaned.partition("@")
    if not separator or not local or "." not in domain:
        raise ValueError("email must be a valid email address")
    return cleaned


class RegisterRequest(BaseModel):
    """New account registration input."""

    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _validate_email_format(value)

    @field_validator("display_name")
    @classmethod
    def display_name_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("display_name must not be blank")
        return value.strip()


class LoginRequest(BaseModel):
    """Credential input for bearer token issuance."""

    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _validate_email_format(value)


class TokenResponse(BaseModel):
    """Bearer token payload. Contains no user data."""

    access_token: str
    token_type: str = "bearer"
