from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class MemoryEntryModel(TimestampMixin, Base):
    __tablename__ = "memory_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    memory_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    importance: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )

    __table_args__ = (
        Index("ix_memory_entries_session_type", "session_id", "memory_type"),
        Index("ix_memory_entries_session_created", "session_id", "created_at"),
        Index("ix_memory_entries_importance", "importance"),
    )
