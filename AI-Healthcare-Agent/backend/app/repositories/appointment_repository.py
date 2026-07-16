import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.database.enums import AppointmentStatus
from app.models.appointment import Appointment, AppointmentAuditLog, DoctorAvailability
from app.repositories.base import BaseRepository


def _ensure_aware(dt: datetime) -> datetime:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self, db: Session):
        super().__init__(db, Appointment)

    def get_by_patient(self, patient_id: uuid.UUID, status: Optional[str] = None) -> list[Appointment]:
        query = select(Appointment).where(Appointment.patient_id == patient_id)
        if status:
            try:
                status_enum = AppointmentStatus(status)
                query = query.where(Appointment.status == status_enum)
            except ValueError:
                pass
        query = query.order_by(Appointment.scheduled_at.desc())
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_doctor(self, doctor_id: uuid.UUID, status: Optional[str] = None) -> list[Appointment]:
        query = select(Appointment).where(Appointment.doctor_id == doctor_id)
        if status:
            try:
                status_enum = AppointmentStatus(status)
                query = query.where(Appointment.status == status_enum)
            except ValueError:
                pass
        query = query.order_by(Appointment.scheduled_at.desc())
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_upcoming_by_patient(self, patient_id: uuid.UUID) -> list[Appointment]:
        now = datetime.now(timezone.utc)
        query = (
            select(Appointment)
            .where(
                Appointment.patient_id == patient_id,
                Appointment.scheduled_at >= now,
                Appointment.status.in_(["scheduled", "confirmed"]),
            )
            .order_by(Appointment.scheduled_at.asc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_doctor_and_time_range(
        self, doctor_id: uuid.UUID, start: datetime, end: datetime, exclude_id: Optional[uuid.UUID] = None
    ) -> list[Appointment]:
        query = select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_at < end,
            Appointment.status.notin_(["cancelled"]),
        )
        if exclude_id:
            query = query.where(Appointment.id != exclude_id)
        result = self.db.execute(query)
        candidates = list(result.scalars().all())
        overlapping = []
        for appt in candidates:
            appt_end = _ensure_aware(appt.scheduled_at) + timedelta(minutes=appt.duration_minutes)
            if appt_end > start:
                overlapping.append(appt)
        return overlapping

    def count_by_doctor_and_date_range(self, doctor_id: uuid.UUID, start: datetime, end: datetime) -> int:
        query = select(func.count(Appointment.id)).where(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_at >= start,
            Appointment.scheduled_at < end,
            Appointment.status.notin_(["cancelled"]),
        )
        return self.db.execute(query).scalar() or 0

    def get_reminder_due(self, reminder_hours: list[int]) -> list[Appointment]:
        now = datetime.now(timezone.utc)
        conditions = []
        for hours in reminder_hours:
            target = now + timedelta(hours=hours)
            target_lower = target.replace(second=0, microsecond=0)
            target_upper = target_lower + timedelta(minutes=1)
            conditions.append(
                and_(
                    Appointment.scheduled_at.between(target_lower, target_upper),
                    Appointment.status.in_(["scheduled", "confirmed"]),
                    or_(Appointment.reminder_sent_at.is_(None), Appointment.reminder_sent_at < now),
                )
            )
        if not conditions:
            return []
        query = select(Appointment).where(or_(*conditions)).order_by(Appointment.scheduled_at.asc())
        result = self.db.execute(query)
        return list(result.scalars().all())


class AuditLogRepository(BaseRepository[AppointmentAuditLog]):
    def __init__(self, db: Session):
        super().__init__(db, AppointmentAuditLog)

    def get_by_appointment(self, appointment_id: uuid.UUID) -> list[AppointmentAuditLog]:
        query = (
            select(AppointmentAuditLog)
            .where(AppointmentAuditLog.appointment_id == appointment_id)
            .order_by(AppointmentAuditLog.timestamp.asc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())


class AvailabilityRepository(BaseRepository[DoctorAvailability]):
    def __init__(self, db: Session):
        super().__init__(db, DoctorAvailability)

    def get_by_doctor(self, doctor_id: uuid.UUID) -> list[DoctorAvailability]:
        query = (
            select(DoctorAvailability)
            .where(DoctorAvailability.doctor_id == doctor_id)
            .order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_doctor_and_day(self, doctor_id: uuid.UUID, day: int) -> list[DoctorAvailability]:
        query = select(DoctorAvailability).where(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.day_of_week == day,
            DoctorAvailability.is_available.is_(True),
        ).order_by(DoctorAvailability.start_time)
        result = self.db.execute(query)
        return list(result.scalars().all())
