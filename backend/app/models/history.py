"""History item ORM model."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HistoryItem(Base):
    """Prototype workspace activity record. No user link yet (auth deferred)."""

    __tablename__ = "history_items"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    related_route: Mapped[str] = mapped_column(String(255), nullable=False)
    item_metadata: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
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
