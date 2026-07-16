import json
import time
from typing import Any, AsyncIterator, Optional

from app.ai.base_provider import BaseProvider
from app.ai.config import AIProviderConfig
from app.ai.exceptions import (
    EmbeddingFailureError,
    InvalidAPIKeyError,
    ModelUnavailableError,
    QuotaExceededError,
    RetryExhaustedError,
    TimeoutError,
)
from app.ai.provider_registry import ProviderRegistry
from app.core.config import settings


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, config: Optional[AIProviderConfig] = None):
        super().__init__(config)
        self._client = None
        self._model = None
        self._embedding_model = None

    def initialize(self) -> None:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.config.api_key)

            self._client = genai
            self._model = genai.GenerativeModel(self.config.model)

            genai_embed_model = self.config.embedding_model
            self._embedding_model = genai_embed_model

            health = self.health_check()
            if health.get("status") != "healthy":
                raise ModelUnavailableError(
                    f"Gemini model '{self.config.model}' is not available: {health.get('error')}"
                )

        except ImportError:
            raise ModelUnavailableError(
                "google-generativeai package is not installed. "
                "Install it with: pip install google-generativeai"
            )
        except Exception as e:
            error_str = str(e).lower()
            if "api key" in error_str or "unauthorized" in error_str or "invalid" in error_str:
                raise InvalidAPIKeyError(f"Invalid Gemini API key: {e}")
            raise ModelUnavailableError(f"Failed to initialize Gemini provider: {e}")

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        for attempt in range(self.config.max_retries):
            try:
                contents = []
                if system_prompt:
                    contents.append({"role": "user", "parts": [system_prompt + "\n\n" + prompt]})
                else:
                    contents.append({"role": "user", "parts": [prompt]})

                response = self._model.generate_content(
                    contents,
                    generation_config=self._generation_config(),
                )
                return response.text

            except Exception as e:
                self._raise_for_error(e)
                if attempt < self.config.max_retries - 1:
                    import time as time_mod
                    time_mod.sleep(self.config.retry_backoff_seconds * (2**attempt))
                else:
                    raise RetryExhaustedError(f"Gemini text generation failed after {self.config.max_retries} retries: {e}")

    def generate_structured_output(
        self, prompt: str, output_schema: dict, system_prompt: Optional[str] = None
    ) -> dict:
        for attempt in range(self.config.max_retries):
            try:
                schema_json = json.dumps(output_schema, indent=2)
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"
                full_prompt += f"\n\nReturn ONLY a valid JSON object matching this schema:\n{schema_json}"

                response = self._model.generate_content(
                    full_prompt,
                    generation_config=self._generation_config(),
                )
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[-1]
                    text = text.rsplit("```", 1)[0].strip()
                return json.loads(text)

            except json.JSONDecodeError:
                if attempt < self.config.max_retries - 1:
                    import time as time_mod
                    time_mod.sleep(self.config.retry_backoff_seconds * (2**attempt))
                    continue
                raise
            except Exception as e:
                self._raise_for_error(e)
                if attempt < self.config.max_retries - 1:
                    import time as time_mod
                    time_mod.sleep(self.config.retry_backoff_seconds * (2**attempt))
                else:
                    raise RetryExhaustedError(f"Gemini structured output failed after {self.config.max_retries} retries: {e}")

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        try:
            import google.generativeai as genai

            result = genai.embed_content(
                model=self._embedding_model,
                content=texts,
            )
            return result["embedding"]
        except Exception as e:
            raise EmbeddingFailureError(f"Gemini embedding failed: {e}")

    async def stream_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [system_prompt + "\n\n" + prompt]})
        else:
            contents.append({"role": "user", "parts": [prompt]})

        response = self._model.generate_content(
            contents,
            generation_config=self._generation_config(),
            stream=True,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def count_tokens(self, text: str) -> int:
        try:
            response = self._model.count_tokens(text)
            return response.total_tokens
        except Exception:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))

    def health_check(self) -> dict:
        try:
            import google.generativeai as genai
            models = genai.list_models()
            available = any(m.name.endswith(self.config.model) for m in models)
            if not available:
                models_named = [m.name for m in models if "generateContent" in m.supported_generation_methods]
                return {
                    "status": "unhealthy",
                    "error": f"Model '{self.config.model}' not found. Available: {models_named[:5]}",
                }
            return {"status": "healthy", "model": self.config.model}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def close(self) -> None:
        self._client = None
        self._model = None

    def _generation_config(self) -> dict:
        return {
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
        }

    def _raise_for_error(self, error: Exception) -> None:
        error_str = str(error).lower()
        if "quota" in error_str or "rate" in error_str or "resource exhausted" in error_str:
            raise QuotaExceededError(f"Gemini quota exceeded: {error}")
        if "timeout" in error_str or "deadline" in error_str:
            raise TimeoutError(f"Gemini request timed out: {error}")
        if "api key" in error_str or "unauthorized" in error_str or "invalid" in error_str or "permission" in error_str:
            raise InvalidAPIKeyError(f"Invalid Gemini API key: {error}")
        if "not found" in error_str or "model" in error_str:
            raise ModelUnavailableError(f"Gemini model unavailable: {error}")


ProviderRegistry.register("gemini", GeminiProvider)
