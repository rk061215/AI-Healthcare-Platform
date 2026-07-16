import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.database.enums import RiskLevel


class EmergencyAlert(TimestampMixin, Base):
    __tablename__ = "emergency_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_level: Mapped[RiskLevel] = mapped_column(nullable=False, index=True)
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", back_populates="emergency_alerts")
    acknowledged_by_doctor = relationship("Doctor", back_populates="acknowledged_alerts")

    __table_args__ = (
        Index("ix_emergency_alerts_risk_acknowledged", "risk_level", "is_acknowledged"),
        Index("ix_emergency_alerts_patient_created", "patient_id", "created_at"),
        CheckConstraint(
            "resolved_at IS NULL OR resolved_at >= created_at",
            name="ck_emergency_resolved_after_created",
        ),
    )
