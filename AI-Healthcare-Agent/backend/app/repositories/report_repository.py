import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: Session):
        super().__init__(db, Report)

    def get_by_patient(self, patient_id: uuid.UUID) -> list[Report]:
        query = (
            select(Report)
            .where(Report.patient_id == patient_id)
            .order_by(Report.uploaded_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_pending_reports(self) -> list[Report]:
        query = select(Report).where(Report.status == "pending")
        result = self.db.execute(query)
        return list(result.scalars().all())
