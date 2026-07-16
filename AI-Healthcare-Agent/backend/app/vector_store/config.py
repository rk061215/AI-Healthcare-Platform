from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.core.config import settings


@dataclass
class VectorStoreConfig:
    provider: str = ""
    collection_name: str = "document_chunks"
    persist_directory: str = "./chromadb_data"
    host: str = "localhost"
    port: int = 8001
    distance_function: str = "cosine"
    batch_size: int = 100
    max_retries: int = 3
    timeout_seconds: int = 30

    def __post_init__(self) -> None:
        if not self.provider:
            self.provider = "chromadb"
        if not self.collection_name and hasattr(settings, "CHROMA_COLLECTION_NAME"):
            self.collection_name = settings.CHROMA_COLLECTION_NAME
