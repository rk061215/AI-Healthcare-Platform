import uuid
from typing import Optional

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin


class PatientDoctor(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "patient_doctors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False
    )

    patient = relationship("Patient", back_populates="doctor_assignments")
    doctor = relationship("Doctor", back_populates="patient_assignments")

    __table_args__ = (
        UniqueConstraint("patient_id", "doctor_id", name="uq_patient_doctor"),
    )
