import uuid
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.adherence_log import AdherenceLog
from app.repositories.base import BaseRepository


class AdherenceRepository(BaseRepository[AdherenceLog]):
    def __init__(self, db: Session):
        super().__init__(db, AdherenceLog)

    def get_by_patient(
        self,
        patient_id: uuid.UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[AdherenceLog]:
        query = select(AdherenceLog).where(AdherenceLog.patient_id == patient_id)
        if start_date:
            query = query.where(AdherenceLog.scheduled_time >= start_date)
        if end_date:
            query = query.where(AdherenceLog.scheduled_time <= end_date)
        query = query.order_by(AdherenceLog.scheduled_time.desc())
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_medicine(
        self, medicine_id: uuid.UUID, limit: int = 30
    ) -> list[AdherenceLog]:
        query = (
            select(AdherenceLog)
            .where(AdherenceLog.medicine_id == medicine_id)
            .order_by(AdherenceLog.scheduled_time.desc())
            .limit(limit)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_today_logs(self, patient_id: uuid.UUID) -> list[AdherenceLog]:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        query = (
            select(AdherenceLog)
            .where(
                AdherenceLog.patient_id == patient_id,
                AdherenceLog.scheduled_time >= today_start,
            )
            .order_by(AdherenceLog.scheduled_time.asc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_stats(
        self,
        patient_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        query = (
            select(
                func.count(AdherenceLog.id).label("total"),
                func.sum(
                    case((AdherenceLog.status == "taken", 1), else_=0)
                ).label("taken"),
                func.sum(
                    case((AdherenceLog.status == "missed", 1), else_=0)
                ).label("missed"),
            )
            .where(
                AdherenceLog.patient_id == patient_id,
                AdherenceLog.scheduled_time >= start_date,
                AdherenceLog.scheduled_time <= end_date,
            )
        )
        result = self.db.execute(query).one()
        return {
            "total": result.total or 0,
            "taken": result.taken or 0,
            "missed": result.missed or 0,
        }
