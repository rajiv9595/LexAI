"""Assistant conversation and message ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.research import ResearchRecord


class AssistantConversation(Base):
    """Prototype assistant conversation thread."""

    __tablename__ = "assistant_conversations"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    prototype: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    user_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    messages: Mapped[list["AssistantMessage"]] = relationship(
        "AssistantMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AssistantMessage.id",
    )


class AssistantMessage(Base):
    """Single prototype message inside a conversation."""

    __tablename__ = "assistant_messages"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    prototype: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    conversation: Mapped[AssistantConversation] = relationship(
        "AssistantConversation", back_populates="messages"
    )

    references: Mapped[list["AssistantMessageReference"]] = relationship(
        "AssistantMessageReference",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="AssistantMessageReference.position",
    )


class AssistantMessageReference(Base):
    """Persisted STEP 20 validated reference with generation-time snapshot.

    STEP 23 provenance (Option B): the composite key binds one assistant
    message to one canonical research record, while the snapshot columns
    preserve exactly what LexAssist used at generation time. Historical
    display MUST read the snapshot columns — never re-resolve from the
    live research record, which may change after generation.

    ``position`` preserves the exact validated-reference order: neither
    database row order nor ``created_at`` timestamps (identical within one
    transaction) can be relied upon for ordering.
    """

    __tablename__ = "assistant_message_references"

    message_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("assistant_messages.id", ondelete="CASCADE"),
        primary_key=True,
    )
    research_record_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("research_records.id", ondelete="RESTRICT"),
        primary_key=True,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    citation_label: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prototype: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    message: Mapped[AssistantMessage] = relationship(
        "AssistantMessage", back_populates="references"
    )
    research_record: Mapped["ResearchRecord"] = relationship("ResearchRecord")
