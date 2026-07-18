import warnings
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_JWT_SECRET = "change-me-to-a-random-secret-key"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    PROJECT_NAME: str = "AI Healthcare Assistant API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Database
    DATABASE_URL: str = "postgresql://neondb_owner:npg_wyaN8m5pdIgM@ep-holy-tree-au74ocm0.c-10.us-east-1.aws.neon.tech/neondb?sslmode=require"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Checkpoint Provider
    CHECKPOINT_PROVIDER: str = "in_memory"

    # JWT
    JWT_SECRET_KEY: str = DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_REFRESH_TOKEN_REMEMBER_ME_DAYS: int = 30

    # AI Provider (vendor-agnostic abstraction)
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_BASE_URL: str = ""
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "text-embedding-004"

    # OpenAI (legacy / fallback)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 2048

    # Google Cloud Vision
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # OCR
    OCR_ENGINE: str = "tesseract"
    OCR_PRIMARY_PROVIDER: str = "tesseract"
    OCR_USE_MOCK: bool = False
    OCR_FALLBACK_PROVIDER: str = "tesseract"
    OCR_RETRY_MAX_ATTEMPTS: int = 3
    OCR_RETRY_BACKOFF_SECONDS: float = 2.0
    OCR_MIN_CONFIDENCE: float = 0.5
    OCR_ENABLED: bool = True
    OCR_GOOGLE_VISION_TIMEOUT: int = 60
    OCR_IMAGE_DPI: int = 300
    OCR_PREPROCESS_ENABLE: bool = True
    OCR_PREPROCESS_DENOISE: bool = True
    OCR_PREPROCESS_DESKEW: bool = True
    OCR_PREPROCESS_BINARIZE: bool = True

    # Tesseract OCR
    TESSERACT_CMD: str = ""
    OCR_LANGUAGE: str = "eng"
    OCR_TIMEOUT: int = 120

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION_NAME: str = "report_embeddings"
    CHROMA_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Security
    SECURITY_HEADERS_ENABLED: bool = True
    ENABLE_CSRF_PROTECTION: bool = True

    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",")]

    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = ".pdf,.jpg,.jpeg,.png,.dicom"

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [e.strip() for e in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def upload_path(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    # Document Storage
    DOCUMENT_STORAGE_DIR: str = "./documents"
    DOCUMENT_MAX_SIZE_MB: int = 20
    DOCUMENT_ALLOWED_EXTENSIONS: str = ".pdf,.png,.jpg,.jpeg"

    @property
    def document_allowed_extensions_list(self) -> List[str]:
        return [e.strip() for e in self.DOCUMENT_ALLOWED_EXTENSIONS.split(",")]

    @property
    def document_storage_path(self) -> Path:
        path = Path(self.DOCUMENT_STORAGE_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PROVIDER: str = "in_memory"
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Redis (optional, for production rate limiting)
    REDIS_URL: str = ""

    @property
    def redis_enabled(self) -> bool:
        return bool(self.REDIS_URL)

    # Appointment Management
    APPOINTMENT_DURATION_MINUTES: int = 30
    APPOINTMENT_MIN_ADVANCE_HOURS: int = 1
    APPOINTMENT_MAX_DAYS_AHEAD: int = 90
    APPOINTMENT_CANCELLATION_WINDOW_HOURS: int = 24
    APPOINTMENT_REMINDER_HOURS_BEFORE: list[int] = [24, 2]
    DEFAULT_TIMEZONE: str = "UTC"

    # Background Tasks
    REMINDER_CHECK_INTERVAL_MINUTES: int = 15

    # Backup
    BACKUP_DIR: str = "./backups"
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_SCHEDULE_CRON: str = "0 3 * * *"  # daily at 3 AM

    # Observability — Logging
    LOG_DIR: str = ""
    LOG_FORMAT: str = "console"  # "json" | "console"

    @property
    def resolved_log_dir(self) -> str:
        if self.LOG_DIR:
            return self.LOG_DIR
        if self._is_container():
            return ""
        return "./logs"

    def _is_container(self) -> bool:
        import os
        return bool(
            self.ENVIRONMENT.lower() in ("production", "staging")
            or os.environ.get("RENDER")
            or os.environ.get("KUBERNETES_SERVICE_HOST")
            or os.environ.get("DOCKER_HOST")
            or os.path.exists("/.dockerenv")
        )

    # Observability — Sentry
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = ""

    # Observability — LangSmith
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "ai-healthcare-dev"
    LANGSMITH_TRACING_SAMPLING_RATE: float = 0.1

    # Observability — OpenTelemetry
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_SERVICE_NAME: str = "ai-healthcare-backend"
    OTEL_TRACE_SAMPLING_RATE: float = 0.1

    # Observability — Prometheus
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp/prometheus"

    def model_post_init(self, _context) -> None:
        if self.JWT_SECRET_KEY == DEFAULT_JWT_SECRET:
            warnings.warn(
                "JWT_SECRET_KEY is set to the default insecure value. "
                "Set a strong random secret via the JWT_SECRET_KEY environment variable in production.",
                stacklevel=2,
            )


settings = Settings()
