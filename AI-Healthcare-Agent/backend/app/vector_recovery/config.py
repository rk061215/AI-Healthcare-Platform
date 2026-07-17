from dataclasses import dataclass, field

from app.core.config import settings
from app.embeddings.base_embedding import BaseEmbedding


@dataclass
class RecoveryConfig:
    enabled: bool = True
    batch_size: int = 5
    batch_delay_seconds: float = 0.5
    max_retries_per_report: int = 3
    retry_delay_seconds: float = 2.0
    rebuild_on_startup: bool = True
    degrade_health_during_rebuild: bool = True

    def __post_init__(self) -> None:
        if hasattr(settings, "VECTOR_RECOVERY_BATCH_SIZE"):
            self.batch_size = int(settings.VECTOR_RECOVERY_BATCH_SIZE)
        if hasattr(settings, "VECTOR_RECOVERY_BATCH_DELAY"):
            self.batch_delay_seconds = float(settings.VECTOR_RECOVERY_BATCH_DELAY)


def get_embedding_model_key(embedding_service=None) -> str:
    if embedding_service and hasattr(embedding_service, "provider"):
        try:
            prov = embedding_service.provider
            return f"{prov.provider_name()}:{prov.model_name()}"
        except Exception:
            pass
    return f"{settings.EMBEDDING_PROVIDER}:{settings.EMBEDDING_MODEL}"
