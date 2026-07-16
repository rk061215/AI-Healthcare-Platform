from typing import Optional, Type

from app.ai.base_provider import BaseProvider


class ProviderRegistry:
    _providers: dict[str, Type[BaseProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[BaseProvider]) -> None:
        cls._providers[name] = provider_cls

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseProvider]]:
        return cls._providers.get(name)

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def unregister(cls, name: str) -> None:
        cls._providers.pop(name, None)
