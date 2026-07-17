"""add_vector_index_state

Adds the vector_index_state table for tracking which reports have
been indexed into the vector store (ChromaDB). Enables automatic
incremental rebuild of the vector index from PostgreSQL source data.

The table stores per-report indexing status, version information,
and checksums — enabling the RecoveryManager to detect exactly
what needs to be rebuilt after any failure or version change.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-16
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "vector_index_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_model_version", sa.String(100), nullable=False),
        sa.Column("chunk_version", sa.String(50), nullable=False, server_default=sa.text("'1.0.0'")),
        sa.Column("schema_version", sa.String(50), nullable=False, server_default=sa.text("'1.0.0'")),
        sa.Column("chunk_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("index_status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("index_checksum", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(op.f("ix_vector_index_state_report_id"), "vector_index_state", ["report_id"])
    op.create_index(op.f("ix_vector_index_state_patient_id"), "vector_index_state", ["patient_id"])
    op.create_index(op.f("ix_vector_index_state_index_status"), "vector_index_state", ["index_status"])
    op.create_index("ix_vector_index_status_embedding", "vector_index_state", ["index_status", "embedding_model_version"])
    op.create_index("ix_vector_index_patient_status", "vector_index_state", ["patient_id", "index_status"])

    op.execute("""
        CREATE OR REPLACE FUNCTION update_vector_index_state_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_vector_index_state_updated_at ON vector_index_state;
    """)
    op.execute("""
        CREATE TRIGGER trg_vector_index_state_updated_at
            BEFORE UPDATE ON vector_index_state
            FOR EACH ROW
            EXECUTE FUNCTION update_vector_index_state_updated_at();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_vector_index_state_updated_at ON vector_index_state;")
    op.execute("DROP FUNCTION IF EXISTS update_vector_index_state_updated_at();")
    op.drop_table("vector_index_state")
