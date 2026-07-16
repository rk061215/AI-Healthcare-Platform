import hashlib
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings
from app.database.enums import StorageProvider


class StorageBackend(ABC):
    @abstractmethod
    def save(self, file_id: str, content: bytes, content_type: str) -> str:
        ...

    @abstractmethod
    def get(self, file_id: str) -> bytes | None:
        ...

    @abstractmethod
    def delete(self, file_id: str) -> bool:
        ...

    @abstractmethod
    def get_url(self, file_id: str) -> str:
        ...


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: Path | None = None):
        self.base_path = base_path or settings.document_storage_path

    def save(self, file_id: str, content: bytes, content_type: str) -> str:
        file_path = self.base_path / file_id
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        return str(file_path.relative_to(self.base_path))

    def get(self, file_id: str) -> bytes | None:
        file_path = self.base_path / file_id
        if not file_path.exists():
            return None
        return file_path.read_bytes()

    def delete(self, file_id: str) -> bool:
        file_path = self.base_path / file_id
        if not file_path.exists():
            return False
        file_path.unlink()
        return True

    def get_url(self, file_id: str) -> str:
        return f"/api/v1/documents/{file_id}/download"


def compute_content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def get_storage_backend(provider: StorageProvider = StorageProvider.LOCAL) -> StorageBackend:
    if provider == StorageProvider.LOCAL:
        return LocalStorageBackend()
    raise ValueError(f"Unsupported storage provider: {provider}")
