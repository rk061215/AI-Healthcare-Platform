from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.memory.base_memory import BaseMemoryStore
from app.memory.exceptions import MemoryStoreError
from app.memory.models import MemoryEntry, MemoryQuery, MemoryType
from app.models.memory_entry import MemoryEntryModel


class PostgresStore(BaseMemoryStore):
    def __init__(self, session: Optional[Session] = None) -> None:
        if session is not None:
            self._session = session
        else:
            self._session = next(get_db())

    def _to_pydantic(self, model: MemoryEntryModel) -> MemoryEntry:
        return MemoryEntry(
            memory_id=model.memory_id,
            session_id=model.session_id,
            memory_type=MemoryType(model.memory_type),
            content=model.content or {},
            importance=model.importance,
            created_at=model.created_at.replace(tzinfo=None) if model.created_at else datetime.utcnow(),
            updated_at=model.updated_at.replace(tzinfo=None) if model.updated_at else datetime.utcnow(),
            expires_at=model.expires_at.replace(tzinfo=None) if model.expires_at else None,
            metadata=model.metadata_ or {},
        )

    def _to_orm(self, entry: MemoryEntry) -> MemoryEntryModel:
        return MemoryEntryModel(
            memory_id=entry.memory_id,
            session_id=entry.session_id,
            memory_type=entry.memory_type.value,
            content=entry.content,
            importance=entry.importance,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            expires_at=entry.expires_at,
            metadata_=entry.metadata,
        )

    def store(self, entry: MemoryEntry) -> str:
        if not entry.memory_id:
            entry.memory_id = str(uuid.uuid4())
        try:
            orm_entry = self._to_orm(entry)
            self._session.add(orm_entry)
            self._session.commit()
            self._session.refresh(orm_entry)
            return entry.memory_id
        except Exception as exc:
            self._session.rollback()
            raise MemoryStoreError(f"Failed to store memory entry: {exc}") from exc

    def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        stmt = select(MemoryEntryModel).where(
            MemoryEntryModel.memory_id == memory_id
        )
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_pydantic(model)

    def search(self, query: MemoryQuery) -> list[MemoryEntry]:
        stmt = select(MemoryEntryModel)

        if query.session_id:
            stmt = stmt.where(MemoryEntryModel.session_id == query.session_id)
        if query.memory_type:
            stmt = stmt.where(
                MemoryEntryModel.memory_type == query.memory_type.value
            )
        if not query.include_expired:
            stmt = stmt.where(
                (MemoryEntryModel.expires_at.is_(None))
                | (MemoryEntryModel.expires_at > datetime.utcnow())
            )
        if query.min_importance > 0.0:
            stmt = stmt.where(
                MemoryEntryModel.importance >= query.min_importance
            )
        if query.time_range_hours is not None:
            cutoff = datetime.utcnow() - timedelta(hours=query.time_range_hours)
            stmt = stmt.where(MemoryEntryModel.created_at >= cutoff)

        stmt = (
            stmt.order_by(MemoryEntryModel.created_at.desc())
            .limit(query.limit)
        )
        result = self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_pydantic(m) for m in models]

    def update(self, entry: MemoryEntry) -> bool:
        stmt = select(MemoryEntryModel).where(
            MemoryEntryModel.memory_id == entry.memory_id
        )
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return False
        try:
            model.session_id = entry.session_id
            model.memory_type = entry.memory_type.value
            model.content = entry.content
            model.importance = entry.importance
            model.expires_at = entry.expires_at
            model.metadata_ = entry.metadata
            model.updated_at = datetime.utcnow()
            self._session.commit()
            return True
        except Exception as exc:
            self._session.rollback()
            raise MemoryStoreError(f"Failed to update memory entry: {exc}") from exc

    def delete(self, memory_id: str) -> bool:
        stmt = select(MemoryEntryModel).where(
            MemoryEntryModel.memory_id == memory_id
        )
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return False
        try:
            self._session.delete(model)
            self._session.commit()
            return True
        except Exception as exc:
            self._session.rollback()
            raise MemoryStoreError(f"Failed to delete memory entry: {exc}") from exc

    def clear_session(self, session_id: str) -> int:
        stmt = select(MemoryEntryModel).where(
            MemoryEntryModel.session_id == session_id
        )
        result = self._session.execute(stmt)
        models = result.scalars().all()
        count = len(models)
        if count == 0:
            return 0
        try:
            for model in models:
                self._session.delete(model)
            self._session.commit()
            return count
        except Exception as exc:
            self._session.rollback()
            raise MemoryStoreError(
                f"Failed to clear session {session_id}: {exc}"
            ) from exc

    def count(self, session_id: str) -> int:
        stmt = (
            select(func.count(MemoryEntryModel.id))
            .where(MemoryEntryModel.session_id == session_id)
        )
        result = self._session.execute(stmt)
        return result.scalar() or 0

    def list_sessions(self) -> list[str]:
        stmt = select(MemoryEntryModel.session_id).distinct()
        result = self._session.execute(stmt)
        return [row[0] for row in result.all()]

    def health_check(self) -> bool:
        try:
            self._session.execute(select(1))
            return True
        except Exception:
            return False
