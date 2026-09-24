"""Centralized application configuration for the LexAssist prototype API."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables with safe defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "LexAssist API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://lexassist:CHANGE_ME@localhost:5432/lexassist"
    )
    jwt_secret_key: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI Configuration (Step 17)
    ai_enabled: bool = False
    ai_provider: str = "mock"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_fallback_models: str = "gemini-3.5-flash,gemini-3.7-flash,gemini-3.8-flash"


settings = Settings()
