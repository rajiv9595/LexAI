"""Assistant routes. Prototype responses scoped to authenticated user."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.assistant import (
    AssistantConversationListResponse,
    AssistantConversationResponse,
    AssistantMessageRequest,
    AssistantMessageResponse,
)
from app.services import assistant_service
from app.services.assistant_service import MAX_LIST_PAGE_SIZE

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/messages", response_model=AssistantMessageResponse)
def post_message(
    payload: AssistantMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssistantMessageResponse:
    """Accept a user message in a user-owned conversation and return a prototype reply."""
    return assistant_service.send_message(db, current_user.id, payload)


@router.get(
    "/conversations",
    response_model=AssistantConversationListResponse,
)
def list_conversations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=MAX_LIST_PAGE_SIZE),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssistantConversationListResponse:
    """Return a paginated lightweight list of the authenticated user's conversations.

    STEP 24 discovery endpoint: newest activity first (``updated_at``
    DESC, ``conversation_id`` DESC tie-break), with message counts and
    first-user-message previews. No messages, references, prompts, or
    provider data are included; full provenance stays on the detail
    endpoint. Legacy NULL-owned conversations are excluded.
    """
    return assistant_service.list_conversations(
        db, current_user.id, page, page_size
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=AssistantConversationResponse,
)
def read_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssistantConversationResponse:
    """Return a prototype conversation by id if owned by the authenticated user."""
    return assistant_service.get_conversation(db, conversation_id, current_user.id)
