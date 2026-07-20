from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from loguru import logger
from app.core.config import settings


@dataclass
class EmbeddingConfig:
    provider: str = ""
    model: str = ""
    dimension: int = 3072
    batch_size: int = 100
    max_retries: int = 3
    timeout_seconds: int = 30
    api_key: str = ""
    base_url: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.provider:
            self.provider = settings.EMBEDDING_PROVIDER if hasattr(settings, "EMBEDDING_PROVIDER") else "gemini"
        if not self.model:
            self.model = settings.EMBEDDING_MODEL or "models/gemini-embedding-001"
        if hasattr(settings, "EMBEDDING_DIMENSION") and settings.EMBEDDING_DIMENSION:
            self.dimension = int(settings.EMBEDDING_DIMENSION)

        logger.info(f"[EMBEDDING DIAG] EmbeddingConfig.__post_init__ — provider={self.provider!r}, dimension={self.dimension}, has_settings_gemini_key={bool(settings.GEMINI_API_KEY) if hasattr(settings, 'GEMINI_API_KEY') else 'NO_ATTR'}")

        if not self.api_key and self.provider == "gemini":
            self.api_key = settings.GEMINI_API_KEY
            logger.info(f"[EMBEDDING DIAG] EmbeddingConfig — pulled api_key from settings.GEMINI_API_KEY: exists={bool(self.api_key)} length={len(self.api_key)}")
        if not self.api_key and self.provider == "openai":
            self.api_key = settings.OPENAI_API_KEY or ""
            logger.info(f"[EMBEDDING DIAG] EmbeddingConfig — pulled api_key from settings.OPENAI_API_KEY: exists={bool(self.api_key)} length={len(self.api_key)}")
        if not self.api_key:
            logger.warning(f"[EMBEDDING DIAG] EmbeddingConfig — FINAL api_key is EMPTY after all lookups")
