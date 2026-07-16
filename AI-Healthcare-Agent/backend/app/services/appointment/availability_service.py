from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.appointment import Appointment, DoctorAvailability
from app.repositories.appointment_repository import AppointmentRepository, AvailabilityRepository


class AppointmentAvailabilityService:
    def __init__(self, db: Session):
        self.db = db
        self.appointment_repo = AppointmentRepository(db)
        self.availability_repo = AvailabilityRepository(db)

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

    def set_availability(self, doctor_id: str, slots_data: list[dict]) -> list[dict]:
        doctor_uuid = self._uuid(doctor_id)
        existing = self.availability_repo.get_by_doctor(doctor_uuid)
        for slot in existing:
            self.db.delete(slot)
        self.db.flush()

        for slot in slots_data:
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

        self.db.commit()
        return self.get_availability(doctor_id)

    def get_available_slots(self, doctor_id: str, date_str: str) -> list[dict]:
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
        now = datetime.now(timezone.utc)

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

    def _uuid(self, value: str):
        import uuid
        return uuid.UUID(value)
