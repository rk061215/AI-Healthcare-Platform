from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictException
from app.models.appointment import Appointment, RecurringAppointment
from app.repositories.appointment_repository import AppointmentRepository


class AppointmentRecurringService:
    def __init__(self, db: Session, appointment_repo: Optional[AppointmentRepository] = None):
        self.db = db
        self.appointment_repo = appointment_repo or AppointmentRepository(db)

    def create_recurring(
        self,
        first_appointment: Appointment,
        data: dict,
    ) -> list[Appointment]:
        recurring = RecurringAppointment(
            appointment_id=first_appointment.id,
            frequency=data["frequency"],
            interval_count=data.get("interval_count", 1),
            weekdays=",".join(str(d) for d in data["weekdays"]) if data.get("weekdays") else None,
            end_date=data.get("end_date"),
            max_occurrences=data.get("max_occurrences"),
            occurrences_generated=0,
        )
        self.db.add(recurring)
        self.db.flush()

        generated = [first_appointment]
        current = first_appointment.scheduled_at
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
                            first_appointment.doctor_id, dt, first_appointment.duration_minutes
                        )
                        if conflict:
                            continue
                        new_appt = Appointment(
                            patient_id=first_appointment.patient_id,
                            doctor_id=first_appointment.doctor_id,
                            title=first_appointment.title,
                            description=first_appointment.description,
                            scheduled_at=dt,
                            duration_minutes=first_appointment.duration_minutes,
                            timezone=first_appointment.timezone,
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
                conflict = self._check_conflict(first_appointment.doctor_id, current, first_appointment.duration_minutes)
                if conflict:
                    continue
                new_appt = Appointment(
                    patient_id=first_appointment.patient_id,
                    doctor_id=first_appointment.doctor_id,
                    title=first_appointment.title,
                    description=first_appointment.description,
                    scheduled_at=current,
                    duration_minutes=first_appointment.duration_minutes,
                    timezone=first_appointment.timezone,
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

    def _check_conflict(
        self, doctor_id, scheduled_at, duration_minutes, exclude_id=None
    ):
        end_time = scheduled_at + timedelta(minutes=duration_minutes)
        conflicts = self.appointment_repo.get_by_doctor_and_time_range(
            doctor_id, scheduled_at, end_time, exclude_id
        )
        return conflicts[0] if conflicts else None
