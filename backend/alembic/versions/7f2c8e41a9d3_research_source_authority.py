"""Add source authority metadata.

Revision ID: 7f2c8e41a9d3
Revises: 6b4d9d4b1c21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "7f2c8e41a9d3"
down_revision: Union[str, Sequence[str], None] = "6b4d9d4b1c21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("research_records", sa.Column("source_url", sa.String(length=2048), nullable=True))
    op.add_column("research_records", sa.Column("publisher", sa.String(length=255), nullable=True))
    op.add_column("research_records", sa.Column("authority_level", sa.String(length=32), nullable=False, server_default="prototype"))
    op.add_column("research_records", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("research_records", "verified_at")
    op.drop_column("research_records", "authority_level")
    op.drop_column("research_records", "publisher")
    op.drop_column("research_records", "source_url")
