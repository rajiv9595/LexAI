"""Assistant data access through SQLAlchemy sessions."""

from sqlalchemy.orm import Session

from app.models.assistant import AssistantConversation, AssistantMessage


def get_conversation(
    db: Session, conversation_id: str, user_id: str
) -> AssistantConversation | None:
    """Return a prototype conversation with messages if owned by the user."""
    return (
        db.query(AssistantConversation)
        .filter(
            AssistantConversation.id == conversation_id,
            AssistantConversation.user_id == user_id,
        )
        .first()
    )


def get_or_create_conversation(
    db: Session, conversation_id: str, user_id: str
) -> AssistantConversation | None:
    """Return the conversation if owned by user, creating an empty thread if missing.

    Returns None if the conversation belongs to another user or has NULL ownership.
    """
    conversation = db.get(AssistantConversation, conversation_id)
    if conversation is None:
        conversation = AssistantConversation(
            id=conversation_id, user_id=user_id, prototype=True
        )
        db.add(conversation)
        db.flush()
        return conversation

    if conversation.user_id != user_id:
        return None

    return conversation


def save_message(
    db: Session, conversation_id: str, role: str, content: str
) -> AssistantMessage:
    """Append a message to a conversation within the current transaction."""
    count = (
        db.query(AssistantMessage)
        .filter(AssistantMessage.conversation_id == conversation_id)
        .count()
    )
    message = AssistantMessage(
        id=f"{conversation_id}-message-{count + 1}",
        conversation_id=conversation_id,
        role=role,
        content=content,
        prototype=True,
    )
    db.add(message)
    db.flush()
    return message
