"""add normalized evidence passages for research records

Revision ID: 6b4d9d4b1c21
Revises: ef0bf391ed04
Create Date: 2026-10-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "6b4d9d4b1c21"
down_revision: Union[str, Sequence[str], None] = "ef0bf391ed04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_evidence",
        sa.Column("id", sa.String(length=160), nullable=False),
        sa.Column("research_record_id", sa.String(length=160), nullable=False),
        sa.Column("locator", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["research_record_id"],
            ["research_records.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_research_evidence_research_record_id",
        "research_evidence",
        ["research_record_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_research_evidence_research_record_id",
        table_name="research_evidence",
    )
    op.drop_table("research_evidence")
