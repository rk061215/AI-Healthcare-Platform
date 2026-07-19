"""add_doctor_timezone

Add timezone column to doctors table.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-19
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("doctors", sa.Column("timezone", sa.String(50), nullable=False, server_default=sa.text("'UTC'")))


def downgrade() -> None:
    op.drop_column("doctors", "timezone")
