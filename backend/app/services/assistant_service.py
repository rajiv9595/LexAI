"""Assistant application logic over persisted conversations."""

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai.models.query_understanding import LegalQueryUnderstanding
from app.ai.models.responses import AIRequestMessage, LegalReferenceItem
from app.ai.models.retrieval import GroundedContext
from app.ai.providers.gemini import GeminiError, GeminiRateLimitError
from app.ai.services.assistant_orchestrator import AssistantOrchestrator
from app.core.config import settings
from app.data import mock_data
from app.repositories import assistant_repository
from app.schemas.assistant import (
    AssistantConversationListResponse,
    AssistantConversationResponse,
    AssistantMessageRequest,
    AssistantMessageResponse,
    ValidatedAssistantReference,
)

logger = logging.getLogger(__name__)

#: STEP 24 pagination bounds for the conversation list endpoint.
DEFAULT_LIST_PAGE_SIZE = 20
MAX_LIST_PAGE_SIZE = 100


def _to_validated_reference(item: LegalReferenceItem) -> ValidatedAssistantReference:
    """Map a STEP 20 citation-validated reference to the frontend-safe DTO.

    Only backend-validated metadata is exposed. ``getattr`` defaults keep
    this tolerant of older/stubbed orchestrator results in tests.
    """
    return ValidatedAssistantReference(
        source_id=getattr(item, "source_id", "") or "",
        title=item.title,
        citation_label=getattr(item, "citation", "") or "",
        source_type=getattr(item, "kind", "") or "",
        jurisdiction=getattr(item, "jurisdiction", None),
        prototype=bool(getattr(item, "prototype", True)),
    )


def send_message(
    db: Session, user_id: str, payload: AssistantMessageRequest
) -> AssistantMessageResponse:
    """Store the user message in a user-owned conversation and return a generated or prototype reply."""
    conversation_id = (
        payload.conversation_id or f"conversation-{uuid.uuid4().hex[:8]}"
    )
    conversation = assistant_repository.get_or_create_conversation(
        db, conversation_id, user_id
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    # Extract conversation history for contextual multi-turn generation
    history_messages: list[AIRequestMessage] = [
        AIRequestMessage(role=msg.role, content=msg.content)
        for msg in (conversation.messages or [])
    ]

    clean_user_message = payload.message.strip()
    validated_refs: list[ValidatedAssistantReference] = []

    try:
        # Save incoming user message
        assistant_repository.save_message(
            db, conversation_id, "user", clean_user_message
        )

        # Generate response via AI Orchestrator or Prototype
        if settings.ai_enabled:
            orchestrator = AssistantOrchestrator()

            def _retrieval_resolver(
                query: str, understanding: LegalQueryUnderstanding | None
            ) -> GroundedContext:
                # Local import avoids a hard services->services cycle at module load.
                from app.services import research_service as _research_service

                try:
                    return _research_service.retrieve_grounded(
                        db, query, understanding, limit=5
                    )
                except Exception:
                    logger.warning(
                        "Research retrieval unavailable; continuing without grounding."
                    )
                    from app.ai.models.retrieval import GroundedContext as _GC

                    return _GC(query=query, sources=[], context_text="", source_count=0)

            try:
                legal_response = orchestrator.process_query(
                    user_message=clean_user_message,
                    conversation_history=history_messages,
                    retrieval_resolver=_retrieval_resolver,
                )
                reply_content = legal_response.answer
                # STEP 21: serialize ONLY STEP 20 citation-validated
                # references. Unvalidated model output never reaches the API.
                validated_refs = [
                    _to_validated_reference(item)
                    for item in (getattr(legal_response, "references", None) or [])
                ]
            except GeminiRateLimitError as exc:
                logger.warning("AI assistant rate-limited: %s", str(exc))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "code": "AI_PROVIDER_RATE_LIMITED",
                        "message": "The AI assistant has temporarily reached its usage limit. Please try again later.",
                    },
                ) from exc
            except GeminiError as exc:
                logger.error("AI Assistant generation error: %s", str(exc))
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI assistant service is currently unavailable. Please try again shortly.",
                ) from exc
            except Exception as exc:
                logger.error("Unexpected error during AI assistant processing: %s", str(exc))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while generating the legal assistance response.",
                ) from exc
        else:
            reply_content = mock_data.ASSISTANT_PROTOTYPE_REPLY

        # Save generated/prototype assistant reply
        reply = assistant_repository.save_message(
            db, conversation_id, "assistant", reply_content
        )
        # STEP 23: persist STEP 20 validated references atomically with the
        # reply — same transaction, before commit. Any persistence failure
        # rolls back the message too, so an answer is never stored without
        # its provenance. Only validated DTOs are written; raw model output
        # never reaches the table.
        if validated_refs:
            assistant_repository.save_message_references(
                db, reply.id, validated_refs
            )
        db.commit()
        db.refresh(reply)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Database error saving assistant message: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not store the message.",
        ) from exc

    return AssistantMessageResponse(
        conversation_id=conversation_id,
        message_id=reply.id,
        role="assistant",
        content=reply.content,
        prototype=not settings.ai_enabled,
        references=validated_refs,
    )


def list_conversations(
    db: Session, user_id: str, page: int = 1, page_size: int = 20
) -> AssistantConversationListResponse:
    """Return a paginated lightweight list of the user's conversations.

    STEP 24 discovery endpoint logic. Ownership comes solely from the
    authenticated identity — no client-supplied user id is accepted.
    Raises 422 for out-of-range pagination input.
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="page must be >= 1.",
        )
    if page_size < 1 or page_size > MAX_LIST_PAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"page_size must be between 1 and {MAX_LIST_PAGE_SIZE}.",
        )
    items, total = assistant_repository.list_conversations(
        db, user_id, page, page_size
    )
    return AssistantConversationListResponse(
        items=items, page=page, page_size=page_size, total=total
    )


def get_conversation(
    db: Session, conversation_id: str, user_id: str
) -> AssistantConversationResponse:
    """Return a prototype or AI conversation owned by the user or raise 404."""
    conversation = assistant_repository.get_conversation(
        db, conversation_id, user_id
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return AssistantConversationResponse(
        conversation_id=conversation.id,
        messages=[
            {
                "message_id": message.id,
                "role": message.role,
                "content": message.content,
                # STEP 23: hydrate from the generation-time SNAPSHOT stored
                # on assistant_message_references — never re-resolved from
                # the live research record, which may have changed since.
                # Pre-STEP-23 and sourceless messages yield [].
                "references": [
                    ValidatedAssistantReference(
                        source_id=ref.research_record_id,
                        title=ref.title,
                        citation_label=ref.citation_label,
                        source_type=ref.source_type,
                        jurisdiction=ref.jurisdiction,
                        prototype=ref.prototype,
                    )
                    for ref in sorted(
                        message.references or [], key=lambda r: r.position
                    )
                ],
            }
            for message in conversation.messages
        ],
        prototype=not settings.ai_enabled,
    )
