from typing import Any, AsyncIterator, Optional

from app.ai.base_provider import BaseProvider
from app.ai.config import AIProviderConfig
from app.ai.provider_registry import ProviderRegistry


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def initialize(self) -> None:
        raise NotImplementedError(
            "Anthropic provider is not yet implemented. "
            "Implement all abstract methods to enable Anthropic support."
        )

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        raise NotImplementedError

    def generate_structured_output(
        self, prompt: str, output_schema: dict, system_prompt: Optional[str] = None
    ) -> dict:
        raise NotImplementedError

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    async def stream_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    def count_tokens(self, text: str) -> int:
        raise NotImplementedError

    def health_check(self) -> dict:
        return {"status": "not_implemented", "provider": "anthropic"}

    def close(self) -> None:
        pass


ProviderRegistry.register("anthropic", AnthropicProvider)
