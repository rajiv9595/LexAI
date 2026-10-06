"""Research evidence passages linked to canonical research records."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ResearchEvidence(Base):
    """A source passage stored separately from source-level metadata."""

    __tablename__ = "research_evidence"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    research_record_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("research_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    locator: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
        doc="Human-readable locator such as section, paragraph, or page.",
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
