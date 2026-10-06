"""Centralized runtime configuration for LexAssist."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "LexAssist API"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"
    environment: str = "development"

    database_url: str = (
        "postgresql+psycopg://lexassist:CHANGE_ME@localhost:5432/lexassist"
    )

    jwt_secret_key: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    ai_enabled: bool = False
    ai_provider: str = "mock"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_fallback_models: str = "gemini-3.5-flash,gemini-3.7-flash,gemini-3.8-flash"

    @model_validator(mode="after")
    def validate_runtime_safety(self) -> "Settings":
        """Reject development-only secrets and impossible AI configuration in production."""
        if self.environment.lower() == "production":
            if self.jwt_secret_key == "CHANGE_ME_TO_A_LONG_RANDOM_SECRET":
                raise ValueError("JWT_SECRET_KEY must be explicitly configured in production.")
            if "CHANGE_ME" in self.database_url:
                raise ValueError("DATABASE_URL must be explicitly configured in production.")
            if self.ai_provider == "mock" and self.ai_enabled:
                raise ValueError("AI_PROVIDER=mock cannot be enabled in production.")
        return self


settings = Settings()
