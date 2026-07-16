import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.emergency_alert import EmergencyAlert
from app.repositories.base import BaseRepository


class EmergencyRepository(BaseRepository[EmergencyAlert]):
    def __init__(self, db: Session):
        super().__init__(db, EmergencyAlert)

    def get_by_patient(self, patient_id: uuid.UUID) -> list[EmergencyAlert]:
        query = (
            select(EmergencyAlert)
            .where(EmergencyAlert.patient_id == patient_id)
            .order_by(EmergencyAlert.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_unacknowledged(self) -> list[EmergencyAlert]:
        query = (
            select(EmergencyAlert)
            .where(EmergencyAlert.is_acknowledged == False)
            .order_by(EmergencyAlert.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_high_risk(self) -> list[EmergencyAlert]:
        query = (
            select(EmergencyAlert)
            .where(EmergencyAlert.risk_level == "HIGH")
            .order_by(EmergencyAlert.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def acknowledge(self, alert_id: uuid.UUID, doctor_id: uuid.UUID) -> EmergencyAlert | None:
        alert = self.get(alert_id)
        if not alert:
            return None
        alert.is_acknowledged = True
        alert.acknowledged_by = doctor_id
        self.db.commit()
        self.db.refresh(alert)
        return alert
