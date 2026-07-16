import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.adherence_log import AdherenceLog
from app.repositories.adherence_repository import AdherenceRepository
from app.repositories.medicine_repository import MedicineRepository


class AdherenceService:
    def __init__(self, db: Session):
        self.db = db
        self.adherence_repo = AdherenceRepository(db)
        self.medicine_repo = MedicineRepository(db)

    def log_dose(
        self,
        patient_id: str,
        medicine_id: str,
        scheduled_time: datetime,
        status: str = "taken",
        notes: str | None = None,
    ) -> AdherenceLog:
        log = AdherenceLog(
            patient_id=uuid.UUID(patient_id),
            medicine_id=uuid.UUID(medicine_id),
            scheduled_time=scheduled_time,
            taken_at=datetime.now(timezone.utc) if status == "taken" else None,
            status=status,
            notes=notes,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_today_schedule(self, patient_id: str) -> list[AdherenceLog]:
        return self.adherence_repo.get_today_logs(uuid.UUID(patient_id))

    def get_stats(
        self,
        patient_id: str,
        days: int = 7,
    ) -> dict:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        return self.adherence_repo.get_stats(
            uuid.UUID(patient_id), start_date, end_date
        )
