"""Assistant routes. Prototype responses scoped to authenticated user."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.assistant import (
    AssistantConversationResponse,
    AssistantMessageRequest,
    AssistantMessageResponse,
)
from app.services import assistant_service

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
