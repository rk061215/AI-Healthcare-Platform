"""add_ocr_columns_to_reports

Adds OCR metadata columns to the reports table for tracking OCR processing:
ocr_confidence, ocr_provider, ocr_pages, retry_count, preprocessing_applied.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-14
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("ocr_confidence", sa.Float(), nullable=True))
    op.add_column("reports", sa.Column("ocr_provider", sa.String(50), nullable=True))
    op.add_column("reports", sa.Column("ocr_pages", sa.Integer(), nullable=True))
    op.add_column("reports", sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("reports", sa.Column("preprocessing_applied", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "preprocessing_applied")
    op.drop_column("reports", "retry_count")
    op.drop_column("reports", "ocr_pages")
    op.drop_column("reports", "ocr_provider")
    op.drop_column("reports", "ocr_confidence")
