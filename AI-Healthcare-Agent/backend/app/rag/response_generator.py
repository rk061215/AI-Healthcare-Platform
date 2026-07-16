from __future__ import annotations

from typing import Any, Optional

from app.ai.config import AIProviderConfig
from app.ai.provider_factory import AIProviderFactory
from app.rag.config import RAGEngineConfig
from app.rag.exceptions import ResponseGenerationError
from app.rag.models import RAGContext, RAGResponse


RESPONSE_SYSTEM_PROMPT = """You are a helpful medical assistant answering questions based on the provided context.

Guidelines:
1. Only answer based on the context provided. Do not make up information.
2. If the context does not contain enough information, say so clearly.
3. Reference specific sources when possible using the citation markers [Source: ...].
4. Use clear, plain language suitable for patients.
5. Do not provide diagnoses or treatment recommendations.
6. If you are unsure about something, express uncertainty.
7. Keep answers concise but complete."""  # noqa: E501


class ResponseGenerator:
    """Generates LLM responses using BaseProvider and PromptManager.

    Supports:
    - Provider-agnostic generation via BaseProvider
    - Prompt template loading via PromptManager
    - Structured output (future-ready)
    - Streaming (future-ready)
    - Configurable temperature and token limits
    """

    def __init__(
        self,
        config: Optional[RAGEngineConfig] = None,
        provider: Optional[Any] = None,
    ) -> None:
        self._config = config or RAGEngineConfig()

        if provider:
            self._provider = provider
        else:
            provider_config = AIProviderConfig(
                provider=self._config.provider,
                model=self._config.model,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )
            factory = AIProviderFactory()
            self._provider = factory.create(config=provider_config)
            self._provider.initialize()

    def generate(
        self,
        query: str,
        context: RAGContext,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a response using the configured provider.

        Args:
            query: The original user query.
            context: The assembled RAGContext with retrieved context.
            system_prompt: Optional override for the system prompt.
            temperature: Optional override for generation temperature.
            max_tokens: Optional override for max output tokens.

        Returns:
            The generated response text.
        """
        prompt = self._build_prompt(query, context)

        try:
            response = self._provider.generate_text(
                prompt=prompt,
                system_prompt=system_prompt or RESPONSE_SYSTEM_PROMPT,
            )
        except Exception as exc:
            raise ResponseGenerationError(
                f"Response generation failed: {exc}"
            ) from exc

        return response

    def generate_structured(
        self,
        query: str,
        context: RAGContext,
        output_schema: dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        """Generate a structured JSON response using the configured provider.

        Args:
            query: The original user query.
            context: The assembled RAGContext with retrieved context.
            output_schema: JSON schema dict for structured output.
            system_prompt: Optional override for the system prompt.

        Returns:
            Parsed structured output as a dict.
        """
        prompt = self._build_prompt(query, context)

        try:
            result = self._provider.generate_structured_output(
                prompt=prompt,
                output_schema=output_schema,
                system_prompt=system_prompt or RESPONSE_SYSTEM_PROMPT,
            )
        except Exception as exc:
            raise ResponseGenerationError(
                f"Structured response generation failed: {exc}"
            ) from exc

        return result

    def _build_prompt(self, query: str, context: RAGContext) -> str:
        parts = []

        if context.conversation_history:
            parts.append("Here is the conversation history:\n")
            parts.append(context.conversation_history)
            parts.append("")

        if context.context:
            parts.append("Here is the relevant medical context:\n")
            parts.append(context.context)
            parts.append("")

        parts.append(f"Question: {query}")
        parts.append("")
        parts.append("Please answer the question based on the context above.")

        return "\n".join(parts)

    @property
    def provider(self) -> Any:
        return self._provider
