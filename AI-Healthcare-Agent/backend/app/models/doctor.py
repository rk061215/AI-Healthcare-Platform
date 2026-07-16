from typing import Optional

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class Doctor(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "doctors"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    license_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hospital_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    years_of_experience: Mapped[Optional[int]] = mapped_column(nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")
    patient_assignments = relationship("PatientDoctor", back_populates="doctor", cascade="all, delete-orphan")
    acknowledged_alerts = relationship("EmergencyAlert", back_populates="acknowledged_by_doctor")
    availability_slots = relationship("DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_doctors_specialization", "specialization"),
        Index("ix_doctors_active_created", "is_active", "created_at"),
    )
