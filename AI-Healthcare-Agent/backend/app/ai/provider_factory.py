from typing import Optional

from app.ai.base_provider import BaseProvider
from app.ai.config import AIProviderConfig
from app.ai.exceptions import ProviderNotFoundError
from app.ai.provider_registry import ProviderRegistry


class AIProviderFactory:

    @staticmethod
    def create(provider_name: Optional[str] = None, config: Optional[AIProviderConfig] = None) -> BaseProvider:
        if config is None:
            config = AIProviderConfig()

        name = (provider_name or config.provider).lower()
        provider_cls = ProviderRegistry.get(name)

        if provider_cls is None:
            raise ProviderNotFoundError(
                f"AI provider '{name}' is not registered. "
                f"Available providers: {', '.join(ProviderRegistry.list_providers())}"
            )

        provider = provider_cls(config)
        provider.initialize()
        return provider
