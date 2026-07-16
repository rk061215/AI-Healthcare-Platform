import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.database.enums import AdherenceStatus


class AdherenceLog(TimestampMixin, Base):
    __tablename__ = "adherence_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medicine_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    taken_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AdherenceStatus] = mapped_column(default=AdherenceStatus.PENDING, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    medicine = relationship("Medicine", back_populates="adherence_logs")
    patient = relationship("Patient", back_populates="adherence_logs")

    __table_args__ = (
        Index("ix_adherence_logs_patient_status", "patient_id", "status"),
        Index("ix_adherence_logs_scheduled", "scheduled_time"),
        CheckConstraint(
            "taken_at IS NULL OR taken_at >= scheduled_time",
            name="ck_adherence_taken_after_scheduled",
        ),
    )
