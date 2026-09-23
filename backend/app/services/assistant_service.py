"""Assistant application logic over persisted prototype conversations."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.data import mock_data
from app.repositories import assistant_repository
from app.schemas.assistant import (
    AssistantConversationResponse,
    AssistantMessageRequest,
    AssistantMessageResponse,
)


def send_message(
    db: Session, user_id: str, payload: AssistantMessageRequest
) -> AssistantMessageResponse:
    """Store the user message in a user-owned conversation and return a reply."""
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

    try:
        assistant_repository.save_message(
            db, conversation_id, "user", payload.message.strip()
        )
        reply = assistant_repository.save_message(
            db, conversation_id, "assistant", mock_data.ASSISTANT_PROTOTYPE_REPLY
        )
        db.commit()
        db.refresh(reply)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not store the prototype message.",
        ) from exc

    return AssistantMessageResponse(
        conversation_id=conversation_id,
        message_id=reply.id,
        role="assistant",
        content=reply.content,
        prototype=True,
    )


def get_conversation(
    db: Session, conversation_id: str, user_id: str
) -> AssistantConversationResponse:
    """Return a prototype conversation owned by the user or raise 404."""
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
            }
            for message in conversation.messages
        ],
        prototype=True,
    )
