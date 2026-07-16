from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CheckpointEntry(Base):
    __tablename__ = "checkpoint_entries"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    checkpoint_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )
    state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
