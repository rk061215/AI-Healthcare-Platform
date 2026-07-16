import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.emergency_alert import EmergencyAlert
from app.repositories.emergency_repository import EmergencyRepository


class EmergencyService:
    def __init__(self, db: Session):
        self.db = db
        self.emergency_repo = EmergencyRepository(db)

    def create_alert(
        self,
        patient_id: str,
        risk_level: str,
        symptoms: str,
        analysis: str | None = None,
    ) -> EmergencyAlert:
        alert = EmergencyAlert(
            patient_id=uuid.UUID(patient_id),
            risk_level=risk_level,
            symptoms=symptoms,
            analysis=analysis,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_patient_alerts(self, patient_id: str) -> list[EmergencyAlert]:
        return self.emergency_repo.get_by_patient(uuid.UUID(patient_id))

    def get_all_unacknowledged(self) -> list[EmergencyAlert]:
        return self.emergency_repo.get_unacknowledged()

    def acknowledge_alert(self, alert_id: str, doctor_id: str) -> EmergencyAlert:
        alert = self.emergency_repo.acknowledge(
            uuid.UUID(alert_id), uuid.UUID(doctor_id)
        )
        if not alert:
            raise NotFoundException("EmergencyAlert", alert_id)
        return alert
