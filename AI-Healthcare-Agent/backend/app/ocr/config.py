from dataclasses import dataclass, field

from app.core.config import settings


@dataclass
class OCRConfig:
    engine: str = settings.OCR_ENGINE
    language: str = settings.OCR_LANGUAGE
    dpi: int = settings.OCR_IMAGE_DPI
    timeout_seconds: int = settings.OCR_TIMEOUT
    min_confidence: float = settings.OCR_MIN_CONFIDENCE
    max_retries: int = settings.OCR_RETRY_MAX_ATTEMPTS
    retry_backoff_seconds: float = settings.OCR_RETRY_BACKOFF_SECONDS

    # Preprocessing
    preprocess_enable: bool = settings.OCR_PREPROCESS_ENABLE
    preprocess_denoise: bool = settings.OCR_PREPROCESS_DENOISE
    preprocess_deskew: bool = settings.OCR_PREPROCESS_DESKEW
    preprocess_binarize: bool = settings.OCR_PREPROCESS_BINARIZE

    # Engine-specific
    tesseract_cmd: str = settings.TESSERACT_CMD
    google_vision_credentials: str = settings.GOOGLE_APPLICATION_CREDENTIALS
    google_vision_timeout: int = settings.OCR_GOOGLE_VISION_TIMEOUT

    # Primary / fallback (legacy engine.py support)
    primary_provider: str = settings.OCR_PRIMARY_PROVIDER
    fallback_provider: str = settings.OCR_FALLBACK_PROVIDER
