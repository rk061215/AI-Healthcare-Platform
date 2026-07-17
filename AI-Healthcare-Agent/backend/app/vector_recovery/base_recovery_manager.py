from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.vector_recovery.health import VectorHealth


class BaseRecoveryManager(ABC):
    @abstractmethod
    def check_health(self) -> VectorHealth:
        pass

    @abstractmethod
    def needs_rebuild(self) -> bool:
        pass

    @abstractmethod
    def rebuild_all(self) -> int:
        pass

    @abstractmethod
    def rebuild_report(self, report_id: str) -> bool:
        pass

    @abstractmethod
    def verify_index(self) -> dict:
        pass

    @abstractmethod
    def cleanup_orphans(self) -> int:
        pass

    @abstractmethod
    def show_status(self) -> dict:
        pass

    @abstractmethod
    def run_startup_recovery(self) -> VectorHealth:
        pass
