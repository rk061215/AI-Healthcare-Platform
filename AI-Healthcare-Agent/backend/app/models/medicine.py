import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin
from app.database.enums import MedicineRoute


class Medicine(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "medicines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    route: Mapped[Optional[MedicineRoute]] = mapped_column(nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    report = relationship("Report", back_populates="medicines")
    patient = relationship("Patient", back_populates="medicines")
    adherence_logs = relationship("AdherenceLog", back_populates="medicine", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_medicines_patient_active", "patient_id", "is_active"),
        CheckConstraint("end_date IS NULL OR start_date IS NULL OR end_date >= start_date", name="ck_medicine_date_range"),
    )
