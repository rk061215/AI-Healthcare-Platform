"""add_documents_table

Adds the documents table for secure medical document upload with
versioning, virus scan status, storage abstraction, and metadata.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-14
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("uploaded_by_role", sa.String(20), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("storage_provider", sa.String(20), nullable=False, server_default=sa.text("'local'")),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("virus_scan_status", sa.String(20), nullable=False, server_default=sa.text("'pending_scan'")),
        sa.Column("virus_scan_result", sa.Text(), nullable=True),
        sa.Column("document_group_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_latest_version", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'uploaded'")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_documents_patient_group", "documents", ["patient_id", "document_group_id"])
    op.create_index("ix_documents_patient_type", "documents", ["patient_id", "file_type"])
    op.create_index("ix_documents_group_version", "documents", ["document_group_id", "version"])
    op.create_index("ix_documents_virus_status", "documents", ["virus_scan_status"])

    op.execute("""
        CREATE OR REPLACE FUNCTION update_documents_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_documents_updated_at ON documents;
    """)
    op.execute("""
        CREATE TRIGGER trg_documents_updated_at
            BEFORE UPDATE ON documents
            FOR EACH ROW
            EXECUTE FUNCTION update_documents_updated_at();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_documents_updated_at ON documents;")
    op.execute("DROP FUNCTION IF EXISTS update_documents_updated_at();")
    op.drop_table("documents")
