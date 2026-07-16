import uuid
from typing import Optional

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, SoftDeleteMixin, TimestampMixin
from app.database.enums import DocumentStatus, StorageProvider, VirusScanStatus


class Document(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    uploaded_by_role: Mapped[str] = mapped_column(String(20), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    storage_provider: Mapped[StorageProvider] = mapped_column(
        default=StorageProvider.LOCAL, nullable=False
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    doc_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    virus_scan_status: Mapped[VirusScanStatus] = mapped_column(
        default=VirusScanStatus.PENDING, nullable=False
    )
    virus_scan_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_latest_version: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        default=DocumentStatus.UPLOADED, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    patient = relationship("Patient", back_populates="documents")

    __table_args__ = (
        Index("ix_documents_patient_group", "patient_id", "document_group_id"),
        Index("ix_documents_patient_type", "patient_id", "file_type"),
        Index("ix_documents_group_version", "document_group_id", "version"),
        Index("ix_documents_virus_status", "virus_scan_status"),
    )
