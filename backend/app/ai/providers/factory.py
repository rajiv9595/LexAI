"""Centralized provider factory for resolving active AI providers."""

import logging
from app.ai.providers.base import AIProvider, MockDeterministicAIProvider
from app.ai.providers.gemini import GeminiAIProvider, GeminiConfigurationError
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_ai_provider(provider_name: str | None = None) -> AIProvider:
    """Resolve and return an AIProvider instance based on configuration or explicit parameter.

    Rules:
    - If AI is disabled: returns MockDeterministicAIProvider.
    - If provider is 'mock': returns MockDeterministicAIProvider.
    - If provider is 'gemini': returns GeminiAIProvider.
    - Any unrecognized provider raises GeminiConfigurationError.
    """
    if provider_name is None and not settings.ai_enabled:
        return MockDeterministicAIProvider()

    resolved_name = (provider_name or settings.ai_provider or "mock").strip().lower()

    if resolved_name == "mock":
        return MockDeterministicAIProvider()
    elif resolved_name == "gemini":
        return GeminiAIProvider(
            model_name=settings.gemini_model,
            fallback_models=settings.gemini_fallback_models,
        )
    else:
        raise GeminiConfigurationError(f"Unsupported AI provider configured: '{resolved_name}'")
