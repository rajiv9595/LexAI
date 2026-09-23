"""Prompt templates and versioned instructions for LexAssist AI."""

from app.ai.prompts.legal_assistant import (
    LEGAL_ASSISTANT_PROMPT_VERSION,
    LEGAL_ASSISTANT_SYSTEM_PROMPT,
)
from app.ai.prompts.query_understanding import (
    LEGAL_QUERY_UNDERSTANDING_PROMPT_VERSION,
    LEGAL_QUERY_UNDERSTANDING_SYSTEM_PROMPT,
)

__all__ = [
    "LEGAL_ASSISTANT_PROMPT_VERSION",
    "LEGAL_ASSISTANT_SYSTEM_PROMPT",
    "LEGAL_QUERY_UNDERSTANDING_PROMPT_VERSION",
    "LEGAL_QUERY_UNDERSTANDING_SYSTEM_PROMPT",
]
