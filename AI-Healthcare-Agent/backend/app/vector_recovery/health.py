from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class VectorHealth:
    status: str = "healthy"
    collection_exists: bool = False
    indexed_reports: int = 0
    actual_document_count: int = 0
    pending_rebuild_count: int = 0
    failed_rebuild_count: int = 0
    total_reports: int = 0
    embedding_model_version: str = ""
    last_rebuild_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    rebuild_in_progress: bool = False
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "collection_exists": self.collection_exists,
            "indexed_reports": self.indexed_reports,
            "actual_document_count": self.actual_document_count,
            "pending_rebuild_count": self.pending_rebuild_count,
            "failed_rebuild_count": self.failed_rebuild_count,
            "total_reports": self.total_reports,
            "embedding_model_version": self.embedding_model_version,
            "last_rebuild_at": self.last_rebuild_at.isoformat() if self.last_rebuild_at else None,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
            "rebuild_in_progress": self.rebuild_in_progress,
            "details": self.details,
        }


_rebuild_progress: dict = {
    "in_progress": False,
    "total": 0,
    "completed": 0,
    "failed": 0,
    "started_at": None,
}


def get_rebuild_progress() -> dict:
    return dict(_rebuild_progress)


def set_rebuild_progress(
    in_progress: bool = False,
    total: int = 0,
    completed: int = 0,
    failed: int = 0,
    started_at: Optional[datetime] = None,
) -> None:
    _rebuild_progress["in_progress"] = in_progress
    _rebuild_progress["total"] = total
    _rebuild_progress["completed"] = completed
    _rebuild_progress["failed"] = failed
    _rebuild_progress["started_at"] = started_at
