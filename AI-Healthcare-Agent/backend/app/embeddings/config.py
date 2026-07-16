from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.core.config import settings


@dataclass
class EmbeddingConfig:
    provider: str = ""
    model: str = ""
    dimension: int = 768
    batch_size: int = 100
    max_retries: int = 3
    timeout_seconds: int = 30
    api_key: str = ""
    base_url: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.provider:
            self.provider = settings.EMBEDDING_PROVIDER if hasattr(settings, "EMBEDDING_PROVIDER") else "gemini"
        if not self.model:
            self.model = settings.EMBEDDING_MODEL or "text-embedding-004"
        if not self.api_key and self.provider == "gemini":
            self.api_key = settings.GEMINI_API_KEY
        if not self.api_key and self.provider == "openai":
            self.api_key = settings.OPENAI_API_KEY or ""
