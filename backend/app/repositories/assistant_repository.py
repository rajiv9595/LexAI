"""Assistant data access through SQLAlchemy sessions."""

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.assistant import (
    AssistantConversation,
    AssistantMessage,
    AssistantMessageReference,
)
from app.models.research import ResearchRecord
from app.schemas.assistant import ValidatedAssistantReference

#: STEP 24: server-side preview bound. The list endpoint never ships full
#: user messages; the beginning is preserved and truncation is marked.
PREVIEW_MAX_LENGTH = 160

PREVIEW_TRUNCATION_SUFFIX = "\u2026"


def get_conversation(
    db: Session, conversation_id: str, user_id: str
) -> AssistantConversation | None:
    """Return a prototype conversation with messages if owned by the user.

    Persisted references are eager-loaded with each message; ownership is
    enforced here, so references are only ever reachable through an
    authorized conversation read.
    """
    return (
        db.query(AssistantConversation)
        .options(
            selectinload(AssistantConversation.messages).selectinload(
                AssistantMessage.references
            )
        )
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
    """Append a message to a conversation within the current transaction.

    STEP 24: also bumps the parent conversation's ``updated_at`` so the
    conversation list (ordered by ``updated_at`` DESC) reflects activity.
    No schema change — this only writes the existing column.
    """
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
    db.query(AssistantConversation).filter(
        AssistantConversation.id == conversation_id
    ).update(
        {AssistantConversation.updated_at: func.now()},
        synchronize_session=False,
    )
    db.flush()
    return message


def truncate_preview(content: str) -> str:
    """Bound a user message to a deterministic list preview.

    Preserves the beginning of the message and appends a single
    ellipsis marker when truncation occurred.
    """
    text = (content or "").strip()
    if len(text) <= PREVIEW_MAX_LENGTH:
        return text
    return text[:PREVIEW_MAX_LENGTH].rstrip() + PREVIEW_TRUNCATION_SUFFIX


def _message_sequence(message_id: str) -> int:
    """Extract the trailing numeric sequence from a message id.

    Message ids look like ``{conversation_id}-message-{n}`` where ``n``
    is creation order. Numeric (not lexicographic) comparison keeps
    ``message-10`` after ``message-2`` even when timestamps tie
    (e.g. SQLite second-precision ``CURRENT_TIMESTAMP``).
    """
    try:
        return int(message_id.rsplit("-", 1)[-1])
    except (ValueError, AttributeError):
        return 0


def list_conversations(
    db: Session, user_id: str, page: int, page_size: int
) -> tuple[list[dict], int]:
    """Return one page of the user's conversations with list metadata.

    STEP 24 discovery query. Ownership is enforced here
    (``user_id ==`` excludes legacy NULL-owned rows). Ordering is
    ``updated_at`` DESC with ``id`` DESC as the deterministic tie-break;
    sorting happens in the database, never in the frontend.

    Query strategy (constant queries, no N+1 regardless of page size):

    1. ``COUNT`` of the user's conversations for ``total``.
    2. One paged ``SELECT`` of conversation rows.
    3. One ``GROUP BY`` count query for the page's message counts.
    4. One ``IN`` query for the page's user-authored messages; the
       earliest per conversation is picked in Python by
       ``(created_at, numeric message sequence)``.

    Returns ``(items, total)`` where each item holds
    ``conversation_id``, ``updated_at`` (ISO 8601), ``message_count``,
    and ``first_user_message_preview`` (or ``None``). No messages,
    references, prompts, or provider data are included.
    """
    base_filter = AssistantConversation.user_id == user_id
    total = (
        db.query(func.count(AssistantConversation.id))
        .filter(base_filter)
        .scalar()
        or 0
    )
    offset = (page - 1) * page_size
    conversations = (
        db.query(AssistantConversation)
        .filter(base_filter)
        .order_by(
            AssistantConversation.updated_at.desc(),
            AssistantConversation.id.desc(),
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )
    if not conversations:
        return [], total

    conv_ids = [conv.id for conv in conversations]
    count_rows = (
        db.query(
            AssistantMessage.conversation_id,
            func.count(AssistantMessage.id),
        )
        .filter(AssistantMessage.conversation_id.in_(conv_ids))
        .group_by(AssistantMessage.conversation_id)
        .all()
    )
    counts = {conv_id: count for conv_id, count in count_rows}

    user_messages = (
        db.query(AssistantMessage)
        .filter(
            AssistantMessage.conversation_id.in_(conv_ids),
            AssistantMessage.role == "user",
        )
        .all()
    )
    earliest: dict[str, AssistantMessage] = {}
    for message in user_messages:
        current = earliest.get(message.conversation_id)
        key = (message.created_at, _message_sequence(message.id))
        if current is None or key < (
            current.created_at,
            _message_sequence(current.id),
        ):
            earliest[message.conversation_id] = message

    items = [
        {
            "conversation_id": conv.id,
            "updated_at": conv.updated_at.isoformat()
            if conv.updated_at is not None
            else "",
            "message_count": counts.get(conv.id, 0),
            "first_user_message_preview": truncate_preview(
                earliest[conv.id].content
            )
            if conv.id in earliest
            else None,
        }
        for conv in conversations
    ]
    return items, total


def reference_row_from_validated(
    message_id: str, ref: ValidatedAssistantReference, position: int
) -> AssistantMessageReference:
    """Map a STEP 20/21 validated reference DTO to a persistence row.

    Copies ONLY approved provenance fields: the canonical identity link
    plus the generation-time snapshot. Model text, URLs, prompts, provider
    metadata, and secrets never reach this table.
    """
    return AssistantMessageReference(
        message_id=message_id,
        research_record_id=ref.source_id,
        position=position,
        title=ref.title,
        citation_label=ref.citation_label,
        source_type=ref.source_type,
        jurisdiction=ref.jurisdiction,
        prototype=ref.prototype,
    )


def save_message_references(
    db: Session, message_id: str, refs: list[ValidatedAssistantReference]
) -> int:
    """Persist validated references for a message in the current transaction.

    Deterministic duplicate handling: input is deduped by ``source_id``
    (first-seen position kept), so the composite primary key is never
    violated by repeated input. Every ``source_id`` must correspond to a
    real research record — a dangling reference raises ``ValueError`` so
    the caller rolls back instead of persisting an answer without its
    provenance. Nothing is committed here; the caller owns the transaction.
    """
    deduped: dict[str, ValidatedAssistantReference] = {}
    for ref in refs or []:
        if ref.source_id not in deduped:
            deduped[ref.source_id] = ref
    if not deduped:
        return 0
    existing_ids = {
        row[0]
        for row in db.query(ResearchRecord.id)
        .filter(ResearchRecord.id.in_(list(deduped.keys())))
        .all()
    }
    missing = [rid for rid in deduped if rid not in existing_ids]
    if missing:
        raise ValueError(
            f"Cannot persist references to unknown research records: {missing}"
        )
    for position, ref in enumerate(deduped.values()):
        db.add(reference_row_from_validated(message_id, ref, position))
    db.flush()
    return len(deduped)
