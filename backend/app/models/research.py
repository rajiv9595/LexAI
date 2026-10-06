"""Research record ORM model."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, String, column, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ResearchRecord(Base):
    """Prototype research record. Not an authoritative legal source."""

    __tablename__ = "research_records"
    __table_args__ = (
        CheckConstraint(
            column("authority_level").in_(
                ("prototype", "secondary", "official_government", "court_opinion", "legislation")
            ),
            name="ck_research_records_authority_level",
        ),
    )

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(128), nullable=False)
    date: Mapped[str] = mapped_column(String(64), nullable=False)
    citation_label: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str] = mapped_column(String(2000), nullable=False)
    topics: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    authority_level: Mapped[str] = mapped_column(String(32), nullable=False, default="prototype")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    prototype: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
