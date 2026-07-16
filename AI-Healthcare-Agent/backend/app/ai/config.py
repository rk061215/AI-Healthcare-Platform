from dataclasses import dataclass, field
from typing import Optional

from app.core.config import settings


@dataclass
class AIProviderConfig:
    provider: str = settings.AI_PROVIDER
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 2048
    top_p: float = 1.0
    timeout_seconds: int = 60
    max_retries: int = 3
    retry_backoff_seconds: float = 2.0
    embedding_model: str = ""

    # Provider-specific
    api_key: str = ""
    base_url: Optional[str] = None

    # Safety
    safety_settings: dict = field(default_factory=dict)

    def __post_init__(self):
        provider_lower = self.provider.lower()

        if not self.model:
            defaults = {
                "gemini": settings.GEMINI_MODEL or "gemini-2.0-flash",
                "openai": settings.OPENAI_MODEL or "gpt-4o-mini",
                "ollama": "llama3",
                "vllm": "default",
                "anthropic": "claude-3-haiku-20240307",
            }
            self.model = defaults.get(provider_lower, defaults["gemini"])

        if not self.embedding_model:
            self.embedding_model = settings.EMBEDDING_MODEL or "text-embedding-004"

        if provider_lower == "gemini" and not self.api_key:
            self.api_key = settings.GEMINI_API_KEY
            self.base_url = settings.GEMINI_BASE_URL or None

        if not self.api_key:
            self.api_key = settings.OPENAI_API_KEY or ""

        if not self.timeout_seconds:
            self.timeout_seconds = 60
