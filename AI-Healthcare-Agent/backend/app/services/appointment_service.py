import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException, ValidationException
from app.database.enums import AppointmentStatus, AuditAction
from app.models.appointment import Appointment, AppointmentAuditLog, DoctorAvailability, RecurringAppointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.repositories.appointment_repository import AppointmentRepository, AuditLogRepository, AvailabilityRepository
from app.schemas.pagination import PaginatedResponse


class AppointmentService:
    def __init__(self, db: Session):
        self.db = db
        self.appointment_repo = AppointmentRepository(db)
        self.audit_repo = AuditLogRepository(db)
        self.availability_repo = AvailabilityRepository(db)

    def _uuid(self, value: str) -> uuid.UUID:
        return uuid.UUID(value)

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _ensure_aware(self, dt: datetime) -> datetime:
        if dt is not None and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def _get_appointment(self, appointment_id: str) -> Appointment:
        appointment = self.appointment_repo.get(self._uuid(appointment_id))
        if not appointment:
            raise NotFoundException("Appointment", appointment_id)
        return appointment

    def _check_ownership(self, appointment: Appointment, user_id: str, role: str) -> None:
        if role == "patient" and str(appointment.patient_id) != user_id:
            raise ForbiddenException("You can only access your own appointments")
        if role == "doctor" and str(appointment.doctor_id) != user_id:
            raise ForbiddenException("You can only access your own appointments")

    def _check_doctor_patient_relationship(self, doctor_id: str, patient_id: str) -> bool:
        from app.models.patient_doctor import PatientDoctor
        result = self.db.execute(
            select(PatientDoctor).where(
                PatientDoctor.doctor_id == self._uuid(doctor_id),
                PatientDoctor.patient_id == self._uuid(patient_id),
                PatientDoctor.deleted_at.is_(None),
            )
        ).first()
        return result is not None

    def _check_conflict(
        self, doctor_id: uuid.UUID, scheduled_at: datetime, duration_minutes: int, exclude_id: Optional[uuid.UUID] = None
    ) -> Optional[Appointment]:
        end_time = scheduled_at + timedelta(minutes=duration_minutes)
        conflicts = self.appointment_repo.get_by_doctor_and_time_range(doctor_id, scheduled_at, end_time, exclude_id)
        return conflicts[0] if conflicts else None

    def _check_availability(self, doctor_id: uuid.UUID, scheduled_at: datetime, duration_minutes: int) -> bool:
        day_of_week = scheduled_at.weekday()
        time_str = scheduled_at.strftime("%H:%M")
        slots = self.availability_repo.get_by_doctor_and_day(doctor_id, day_of_week)
        if not slots:
            return True
        slot_end = scheduled_at + timedelta(minutes=duration_minutes)
        slot_end_str = slot_end.strftime("%H:%M")
        for slot in slots:
            if slot.start_time <= time_str and slot_end_str <= slot.end_time:
                return True
        return False

    def _log_audit(
        self,
        appointment_id: uuid.UUID,
        action: str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        changes: Optional[dict] = None,
    ) -> None:
        log = AppointmentAuditLog(
            appointment_id=appointment_id,
            action=action,
            user_id=self._uuid(user_id) if user_id else None,
            user_role=user_role,
            changes=changes,
            timestamp=self._now(),
        )
        self.db.add(log)

    def _build_detail(self, appointment: Appointment) -> dict:
        patient = self.db.get(Patient, appointment.patient_id)
        doctor = self.db.get(Doctor, appointment.doctor_id)
        logs = self.audit_repo.get_by_appointment(appointment.id)
        return {
            "id": str(appointment.id),
            "patient_id": str(appointment.patient_id),
            "doctor_id": str(appointment.doctor_id),
            "title": appointment.title,
            "description": appointment.description,
            "scheduled_at": appointment.scheduled_at.isoformat(),
            "duration_minutes": appointment.duration_minutes,
            "status": appointment.status.value,
            "follow_up_notes": appointment.follow_up_notes,
            "cancellation_reason": appointment.cancellation_reason,
            "cancelled_at": appointment.cancelled_at.isoformat() if appointment.cancelled_at else None,
            "rescheduled_from": str(appointment.rescheduled_from) if appointment.rescheduled_from else None,
            "timezone": appointment.timezone,
            "created_at": appointment.created_at.isoformat(),
            "updated_at": appointment.updated_at.isoformat(),
            "patient_name": patient.full_name if patient else None,
            "patient_phone": patient.phone if patient else None,
            "doctor_name": doctor.full_name if doctor else None,
            "doctor_specialization": doctor.specialization if doctor else None,
            "audit_logs": [
                {
                    "id": str(log.id),
                    "action": log.action,
                    "user_role": log.user_role,
                    "changes": log.changes,
                    "timestamp": log.timestamp.isoformat(),
                }
                for log in logs
            ],
        }

    def create_appointment(
        self, data: dict, user_id: str, role: str
    ) -> Appointment:
        scheduled_at = data["scheduled_at"]
        now = self._now()

        min_advance = now + timedelta(hours=settings.APPOINTMENT_MIN_ADVANCE_HOURS)
        if scheduled_at < min_advance:
            raise ValidationException(
                f"Appointment must be at least {settings.APPOINTMENT_MIN_ADVANCE_HOURS} hour(s) in advance"
            )

        max_ahead = now + timedelta(days=settings.APPOINTMENT_MAX_DAYS_AHEAD)
        if scheduled_at > max_ahead:
            raise ValidationException(
                f"Appointment cannot be more than {settings.APPOINTMENT_MAX_DAYS_AHEAD} days ahead"
            )

        patient_id = data.get("patient_id", user_id) if role == "patient" else user_id
        doctor_id = data["doctor_id"]
        duration = data.get("duration_minutes", settings.APPOINTMENT_DURATION_MINUTES)

        doctor_uuid = self._uuid(doctor_id)
        patient_uuid = self._uuid(patient_id)

        if role == "patient" and patient_id != user_id:
            raise ForbiddenException("Patients can only create appointments for themselves")

        relation = self._check_doctor_patient_relationship(doctor_id, patient_id)
        if not relation:
            from app.models.patient_doctor import PatientDoctor
            pd = PatientDoctor(patient_id=patient_uuid, doctor_id=doctor_uuid, is_active=True)
            self.db.add(pd)
            self.db.flush()

        conflict = self._check_conflict(doctor_uuid, scheduled_at, duration)
        if conflict:
            raise ConflictException(
                f"Time slot conflicts with appointment {conflict.id} "
                f"({conflict.scheduled_at.isoformat()})"
            )

        appointment = Appointment(
            patient_id=patient_uuid,
            doctor_id=doctor_uuid,
            title=data.get("title"),
            description=data.get("description"),
            scheduled_at=scheduled_at,
            duration_minutes=duration,
            timezone=data.get("timezone", "UTC"),
        )
        self.db.add(appointment)
        self.db.flush()

        self._log_audit(
            appointment_id=appointment.id,
            action=AuditAction.CREATED.value,
            user_id=user_id,
            user_role=role,
            changes={"scheduled_at": scheduled_at.isoformat(), "doctor_id": doctor_id},
        )

        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def get_appointment(self, appointment_id: str, user_id: str, role: str) -> dict:
        appointment = self._get_appointment(appointment_id)
        self._check_ownership(appointment, user_id, role)
        return self._build_detail(appointment)

    def list_appointments(
        self,
        user_id: str,
        role: str,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        user_uuid = self._uuid(user_id)

        query = select(Appointment)
        if role == "patient":
            query = query.where(Appointment.patient_id == user_uuid)
        else:
            query = query.where(Appointment.doctor_id == user_uuid)

        if status:
            try:
                status_enum = AppointmentStatus(status)
                query = query.where(Appointment.status == status_enum)
            except ValueError:
                pass

        query = query.order_by(Appointment.scheduled_at.desc())

        total = self.db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

        offset = (page - 1) * per_page
        rows = self.db.execute(query.offset(offset).limit(per_page)).scalars().all()

        items = []
        for a in rows:
            patient = self.db.get(Patient, a.patient_id) if role == "doctor" else None
            doctor = self.db.get(Doctor, a.doctor_id) if role == "patient" else None
            items.append({
                "id": str(a.id),
                "patient_id": str(a.patient_id),
                "doctor_id": str(a.doctor_id),
                "title": a.title,
                "description": a.description,
                "scheduled_at": a.scheduled_at.isoformat(),
                "duration_minutes": a.duration_minutes,
                "status": a.status.value,
                "follow_up_notes": a.follow_up_notes,
                "cancellation_reason": a.cancellation_reason,
                "cancelled_at": a.cancelled_at.isoformat() if a.cancelled_at else None,
                "rescheduled_from": str(a.rescheduled_from) if a.rescheduled_from else None,
                "timezone": a.timezone,
                "created_at": a.created_at.isoformat(),
                "updated_at": a.updated_at.isoformat(),
                "patient_name": patient.full_name if patient else None,
                "doctor_name": doctor.full_name if doctor else None,
                "doctor_specialization": doctor.specialization if doctor else None,
            })

        return PaginatedResponse.create(items, total, page, per_page)

    def update_appointment(
        self, appointment_id: str, data: dict, user_id: str, role: str
    ) -> Appointment:
        appointment = self._get_appointment(appointment_id)
        self._check_ownership(appointment, user_id, role)

        if appointment.status == AppointmentStatus.CANCELLED:
            raise ValidationException("Cannot update a cancelled appointment")
        if appointment.status == AppointmentStatus.COMPLETED:
            raise ValidationException("Cannot update a completed appointment")

        changes = {}
        for key, value in data.items():
            if value is not None and hasattr(appointment, key):
                old = getattr(appointment, key)
                if isinstance(old, datetime):
                    old_str = old.isoformat()
                elif hasattr(old, "value"):
                    old_str = old.value
                else:
                    old_str = old
                if isinstance(value, datetime):
                    new_str = value.isoformat()
                else:
                    new_str = value
                if str(old_str) != str(new_str):
                    changes[key] = {"from": str(old_str), "to": str(new_str)}
                setattr(appointment, key, value)

        if changes:
            self._log_audit(
                appointment_id=appointment.id,
                action=AuditAction.UPDATED.value,
                user_id=user_id,
                user_role=role,
                changes=changes,
            )

        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def cancel_appointment(
        self, appointment_id: str, reason: str, user_id: str, role: str
    ) -> Appointment:
        appointment = self._get_appointment(appointment_id)
        self._check_ownership(appointment, user_id, role)

        if appointment.status == AppointmentStatus.CANCELLED:
            raise ValidationException("Appointment is already cancelled")
        if appointment.status == AppointmentStatus.COMPLETED:
            raise ValidationException("Cannot cancel a completed appointment")

        now = self._now()
        scheduled_at = self._ensure_aware(appointment.scheduled_at)
        if role == "patient" and scheduled_at - now < timedelta(
            hours=settings.APPOINTMENT_CANCELLATION_WINDOW_HOURS
        ):
            raise ValidationException(
                f"Cancellation must be at least {settings.APPOINTMENT_CANCELLATION_WINDOW_HOURS} hours before the appointment"
            )

        previous_status = appointment.status
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = now
        appointment.cancellation_reason = reason

        self._log_audit(
            appointment_id=appointment.id,
            action=AuditAction.CANCELLED.value,
            user_id=user_id,
            user_role=role,
            changes={"reason": reason, "previous_status": previous_status.value if previous_status else None},
        )

        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def reschedule_appointment(
        self, appointment_id: str, scheduled_at: datetime, reason: Optional[str], user_id: str, role: str
    ) -> Appointment:
        appointment = self._get_appointment(appointment_id)
        self._check_ownership(appointment, user_id, role)

        if appointment.status == AppointmentStatus.CANCELLED:
            raise ValidationException("Cannot reschedule a cancelled appointment")
        if appointment.status == AppointmentStatus.COMPLETED:
            raise ValidationException("Cannot reschedule a completed appointment")

        now = self._now()
        min_advance = now + timedelta(hours=settings.APPOINTMENT_MIN_ADVANCE_HOURS)
        if scheduled_at < min_advance:
            raise ValidationException(
                f"Rescheduled time must be at least {settings.APPOINTMENT_MIN_ADVANCE_HOURS} hour(s) from now"
            )

        max_ahead = now + timedelta(days=settings.APPOINTMENT_MAX_DAYS_AHEAD)
        if scheduled_at > max_ahead:
            raise ValidationException(
                f"Rescheduled time cannot be more than {settings.APPOINTMENT_MAX_DAYS_AHEAD} days ahead"
            )

        conflict = self._check_conflict(
            appointment.doctor_id, scheduled_at, appointment.duration_minutes, appointment.id
        )
        if conflict:
            raise ConflictException(
                f"New time slot conflicts with appointment {conflict.id} "
                f"({conflict.scheduled_at.isoformat()})"
            )

        old_scheduled_at = appointment.scheduled_at
        appointment.scheduled_at = scheduled_at

        self._log_audit(
            appointment_id=appointment.id,
            action=AuditAction.RESCHEDULED.value,
            user_id=user_id,
            user_role=role,
            changes={
                "from": old_scheduled_at.isoformat(),
                "to": scheduled_at.isoformat(),
                "reason": reason,
            },
        )

        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def delete_appointment(self, appointment_id: str, user_id: str, role: str) -> None:
        appointment = self._get_appointment(appointment_id)
        self._check_ownership(appointment, user_id, role)

        self._log_audit(
            appointment_id=appointment.id,
            action=AuditAction.DELETED.value,
            user_id=user_id,
            user_role=role,
        )

        self.db.delete(appointment)
        self.db.commit()

    def confirm_appointment(self, appointment_id: str, user_id: str, role: str) -> Appointment:
        appointment = self._get_appointment(appointment_id)
        if role == "patient" and str(appointment.patient_id) != user_id:
            raise ForbiddenException("You can only confirm your own appointments")
        if role == "doctor" and str(appointment.doctor_id) != user_id:
            raise ForbiddenException("You can only confirm your own appointments")

        if appointment.status != AppointmentStatus.SCHEDULED:
            raise ValidationException("Only scheduled appointments can be confirmed")

        appointment.status = AppointmentStatus.CONFIRMED

        self._log_audit(
            appointment_id=appointment.id,
            action=AuditAction.CONFIRMED.value,
            user_id=user_id,
            user_role=role,
        )

        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def complete_appointment(
        self, appointment_id: str, follow_up_notes: Optional[str], user_id: str, role: str
    ) -> Appointment:
        appointment = self._get_appointment(appointment_id)
        if role != "doctor" or str(appointment.doctor_id) != user_id:
            raise ForbiddenException("Only the assigned doctor can complete appointments")

        if appointment.status not in (AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS):
            raise ValidationException("Only confirmed or in-progress appointments can be completed")

        appointment.status = AppointmentStatus.COMPLETED
        if follow_up_notes:
            appointment.follow_up_notes = follow_up_notes

        self._log_audit(
            appointment_id=appointment.id,
            action=AuditAction.COMPLETED.value,
            user_id=user_id,
            user_role=role,
            changes={"follow_up_notes": follow_up_notes} if follow_up_notes else None,
        )

        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def create_recurring_appointment(
        self, data: dict, user_id: str, role: str
    ) -> list[Appointment]:
        first = self.create_appointment(data, user_id, role)

        recurring = RecurringAppointment(
            appointment_id=first.id,
            frequency=data["frequency"],
            interval_count=data.get("interval_count", 1),
            weekdays=",".join(str(d) for d in data["weekdays"]) if data.get("weekdays") else None,
            end_date=data.get("end_date"),
            max_occurrences=data.get("max_occurrences"),
            occurrences_generated=0,
        )
        self.db.add(recurring)
        self.db.flush()

        generated = [first]
        current = first.scheduled_at
        frequency = data["frequency"]
        interval = data.get("interval_count", 1)
        max_occ = data.get("max_occurrences")
        end_date = data.get("end_date")
        weekdays = data.get("weekdays")

        occurrences = 0
        while True:
            occurrences += 1
            if max_occ and occurrences >= max_occ:
                break
            if end_date and current >= end_date:
                break

            if frequency == "daily":
                current = current + timedelta(days=interval)
            elif frequency == "weekly":
                current = current + timedelta(weeks=interval)
            elif frequency == "biweekly":
                current = current + timedelta(weeks=2 * interval)
            elif frequency == "monthly":
                month = current.month + interval
                year = current.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                try:
                    current = current.replace(year=year, month=month)
                except ValueError:
                    break

            if weekdays and frequency == "weekly":
                matching_days = []
                for d in sorted(weekdays):
                    days_ahead = d - current.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    matching_days.append(current + timedelta(days=days_ahead))
                matching_days.sort()
                for dt in matching_days:
                    if max_occ and occurrences >= max_occ:
                        break
                    if end_date and dt >= end_date:
                        break
                    if dt == matching_days[0]:
                        current = dt
                    else:
                        conflict = self._check_conflict(
                            first.doctor_id, dt, first.duration_minutes
                        )
                        if conflict:
                            continue
                        new_appt = Appointment(
                            patient_id=first.patient_id,
                            doctor_id=first.doctor_id,
                            title=first.title,
                            description=first.description,
                            scheduled_at=dt,
                            duration_minutes=first.duration_minutes,
                            timezone=first.timezone,
                        )
                        self.db.add(new_appt)
                        self.db.flush()
                        generated.append(new_appt)
                        occurrences += 1
                continue

            if max_occ and len(generated) >= max_occ:
                break
            if end_date and current >= end_date:
                break

            try:
                conflict = self._check_conflict(first.doctor_id, current, first.duration_minutes)
                if conflict:
                    continue
                new_appt = Appointment(
                    patient_id=first.patient_id,
                    doctor_id=first.doctor_id,
                    title=first.title,
                    description=first.description,
                    scheduled_at=current,
                    duration_minutes=first.duration_minutes,
                    timezone=first.timezone,
                )
                self.db.add(new_appt)
                self.db.flush()
                generated.append(new_appt)
            except Exception:
                break

        recurring.occurrences_generated = len(generated) - 1
        self.db.commit()

        for appt in generated:
            self.db.refresh(appt)

        return generated

    def get_availability(self, doctor_id: str) -> list[dict]:
        doctor_uuid = self._uuid(doctor_id)
        slots = self.availability_repo.get_by_doctor(doctor_uuid)
        return [
            {
                "id": str(s.id),
                "doctor_id": str(s.doctor_id),
                "day_of_week": s.day_of_week,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "is_available": s.is_available,
                "slot_duration_minutes": s.slot_duration_minutes,
            }
            for s in slots
        ]

    def set_availability(self, doctor_id: str, slots: list[dict]) -> list[dict]:
        doctor_uuid = self._uuid(doctor_id)
        existing = self.availability_repo.get_by_doctor(doctor_uuid)
        for slot in existing:
            self.db.delete(slot)
        self.db.flush()

        created = []
        for slot in slots:
            av = DoctorAvailability(
                doctor_id=doctor_uuid,
                day_of_week=slot["day_of_week"],
                start_time=slot["start_time"],
                end_time=slot["end_time"],
                is_available=slot.get("is_available", True),
                slot_duration_minutes=slot.get("slot_duration_minutes", 30),
            )
            self.db.add(av)
            self.db.flush()
            created.append(av)

        self.db.commit()
        return self.get_availability(doctor_id)

    def get_available_slots(
        self, doctor_id: str, date_str: str
    ) -> list[dict]:
        doctor_uuid = self._uuid(doctor_id)
        try:
            target_date = datetime.fromisoformat(date_str).date()
        except (ValueError, TypeError):
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        day_of_week = target_date.weekday()
        slots = self.availability_repo.get_by_doctor_and_day(doctor_uuid, day_of_week)
        if not slots:
            return []

        day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        existing_appointments = self.appointment_repo.get_by_doctor_and_time_range(
            doctor_uuid, day_start, day_end
        )

        booked_ranges = []
        for appt in existing_appointments:
            appt_end = appt.scheduled_at + timedelta(minutes=appt.duration_minutes)
            booked_ranges.append((appt.scheduled_at, appt_end))

        available = []
        now = self._now()

        for slot in slots:
            hour, minute = map(int, slot.start_time.split(":"))
            slot_start = day_start.replace(hour=hour, minute=minute)

            end_hour, end_minute = map(int, slot.end_time.split(":"))
            slot_end = day_start.replace(hour=end_hour, minute=end_minute)

            current = slot_start
            while current + timedelta(minutes=slot.slot_duration_minutes) <= slot_end:
                if current < now:
                    current += timedelta(minutes=slot.slot_duration_minutes)
                    continue

                slot_end_time = current + timedelta(minutes=slot.slot_duration_minutes)
                is_booked = False
                for b_start, b_end in booked_ranges:
                    if current < b_end and slot_end_time > b_start:
                        is_booked = True
                        break

                if not is_booked:
                    available.append({
                        "start": current.isoformat(),
                        "end": slot_end_time.isoformat(),
                        "doctor_id": doctor_id,
                    })

                current += timedelta(minutes=slot.slot_duration_minutes)

        return available

    def get_audit_logs(self, appointment_id: str, user_id: str, role: str) -> list[dict]:
        appointment = self._get_appointment(appointment_id)
        self._check_ownership(appointment, user_id, role)
        logs = self.audit_repo.get_by_appointment(self._uuid(appointment_id))
        return [
            {
                "id": str(log.id),
                "appointment_id": str(log.appointment_id),
                "action": log.action,
                "user_id": str(log.user_id) if log.user_id else None,
                "user_role": log.user_role,
                "changes": log.changes,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ]

    def send_reminder(self, appointment_id: str) -> Appointment:
        appointment = self._get_appointment(appointment_id)
        appointment.reminder_sent_at = self._now()

        self._log_audit(
            appointment_id=appointment.id,
            action=AuditAction.REMINDER_SENT.value,
        )

        self.db.commit()
        self.db.refresh(appointment)
        return appointment
