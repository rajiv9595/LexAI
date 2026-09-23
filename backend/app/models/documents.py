"""Document draft ORM model."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, String, column, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

DOCUMENT_TYPES = ("rental", "employment", "nda", "will")
DOCUMENT_STATUSES = ("Prototype Draft", "Draft", "Completed")


class Document(Base):
    """Prototype document draft. Not a legally valid document."""

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            column("type").in_(DOCUMENT_TYPES),
            name="ck_documents_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Prototype Draft")
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
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
