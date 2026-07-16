from datetime import datetime
from typing import Optional

from sqlalchemy import Date, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.database.enums import BloodGroup, Gender


class Patient(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "patients"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    date_of_birth: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(nullable=True)
    blood_group: Mapped[Optional[BloodGroup]] = mapped_column(nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    emergency_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    terms_accepted: Mapped[bool] = mapped_column(default=False, nullable=False)
    terms_accepted_at: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)

    reports = relationship("Report", back_populates="patient", cascade="all, delete-orphan")
    medicines = relationship("Medicine", back_populates="patient", cascade="all, delete-orphan")
    chat_messages = relationship("ChatHistory", back_populates="patient", cascade="all, delete-orphan")
    adherence_logs = relationship("AdherenceLog", back_populates="patient", cascade="all, delete-orphan")
    emergency_alerts = relationship("EmergencyAlert", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    doctor_assignments = relationship("PatientDoctor", back_populates="patient", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="patient", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_patients_active_created", "is_active", "created_at"),
    )
