import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class VectorIndexState(TimestampMixin, Base):
    __tablename__ = "vector_index_state"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    embedding_model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    chunk_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    schema_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    index_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    index_checksum: Mapped[str] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    last_indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_vector_index_status_embedding", "index_status", "embedding_model_version"),
        Index("ix_vector_index_patient_status", "patient_id", "index_status"),
    )
