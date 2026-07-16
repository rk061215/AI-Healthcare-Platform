import uuid
from typing import Optional

from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db: Session):
        super().__init__(db, Document)

    def get_by_patient(
        self,
        patient_id: uuid.UUID,
        file_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Document], int]:
        query = select(Document).where(
            and_(Document.patient_id == patient_id, Document.is_active == True)
        )
        count_query = select(Document).where(
            and_(Document.patient_id == patient_id, Document.is_active == True)
        )

        if file_type:
            query = query.where(Document.file_type == file_type)
            count_query = count_query.where(Document.file_type == file_type)

        total = len(self.db.execute(count_query).scalars().all())
        query = query.order_by(Document.uploaded_at.desc()).offset(skip).limit(limit)
        items = list(self.db.execute(query).scalars().all())
        return items, total

    def get_by_group(self, group_id: uuid.UUID) -> list[Document]:
        query = (
            select(Document)
            .where(Document.document_group_id == group_id)
            .order_by(Document.version.asc())
        )
        return list(self.db.execute(query).scalars().all())

    def get_latest_version(self, group_id: uuid.UUID) -> Optional[Document]:
        query = (
            select(Document)
            .where(
                and_(
                    Document.document_group_id == group_id,
                    Document.is_latest_version == True,
                )
            )
        )
        return self.db.execute(query).scalar_one_or_none()

    def get_next_version(self, group_id: uuid.UUID) -> int:
        latest = self.get_latest_version(group_id)
        if not latest:
            return 1
        return latest.version + 1

    def mark_previous_versions_stale(self, group_id: uuid.UUID, exclude_id: uuid.UUID) -> None:
        stmt = (
            update(Document)
            .where(
                and_(
                    Document.document_group_id == group_id,
                    Document.id != exclude_id,
                )
            )
            .values(is_latest_version=False)
        )
        self.db.execute(stmt)
        self.db.commit()

    def get_by_content_hash(
        self, patient_id: uuid.UUID, content_hash: str
    ) -> Optional[Document]:
        query = select(Document).where(
            and_(
                Document.patient_id == patient_id,
                Document.content_hash == content_hash,
                Document.is_active == True,
            )
        )
        return self.db.execute(query).scalar_one_or_none()

    def count_by_patient(self, patient_id: uuid.UUID) -> int:
        query = select(Document).where(
            and_(Document.patient_id == patient_id, Document.is_active == True)
        )
        return len(self.db.execute(query).scalars().all())
