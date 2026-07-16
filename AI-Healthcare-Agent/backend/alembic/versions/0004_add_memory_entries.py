"""add_memory_entries_table

Adds the memory_entries table for the PostgreSQL-based MemoryStore,
supporting session-scoped AI agent memory with JSONB content/metadata.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-16
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "memory_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("memory_id", sa.String(255), nullable=False, unique=True),
        sa.Column("session_id", sa.String(255), nullable=False),
        sa.Column("memory_type", sa.String(50), nullable=False),
        sa.Column("content", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("importance", sa.Float(), nullable=False, server_default=sa.text("0.5")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(op.f("ix_memory_entries_memory_id"), "memory_entries", ["memory_id"])
    op.create_index(op.f("ix_memory_entries_session_id"), "memory_entries", ["session_id"])
    op.create_index("ix_memory_entries_session_type", "memory_entries", ["session_id", "memory_type"])
    op.create_index("ix_memory_entries_session_created", "memory_entries", ["session_id", "created_at"])
    op.create_index("ix_memory_entries_importance", "memory_entries", ["importance"])

    op.execute("""
        CREATE OR REPLACE FUNCTION update_memory_entries_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        DROP TRIGGER IF EXISTS trg_memory_entries_updated_at ON memory_entries;
    """)
    op.execute("""
        CREATE TRIGGER trg_memory_entries_updated_at
            BEFORE UPDATE ON memory_entries
            FOR EACH ROW
            EXECUTE FUNCTION update_memory_entries_updated_at();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_memory_entries_updated_at ON memory_entries;")
    op.execute("DROP FUNCTION IF EXISTS update_memory_entries_updated_at();")
    op.drop_table("memory_entries")
