from __future__ import annotations

from typing import Optional

from app.embeddings.base_embedding import BaseEmbedding
from app.embeddings.config import EmbeddingConfig
from app.embeddings.embedding_registry import EmbeddingRegistry
from app.embeddings.exceptions import (
    EmbeddingFailureError,
)


class GeminiEmbedding(BaseEmbedding):
    """Embedding provider using Google's Gemini embedding models.

    Uses google.generativeai (the existing project SDK).
    Supports text-embedding-004 and other Google embedding models.
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self._config = config or EmbeddingConfig()
        self._model = self._config.model
        self._configured = False

    def initialize(self) -> None:
        import google.generativeai as genai

        api_key = self._config.api_key
        if not api_key:
            raise EmbeddingFailureError(
                "Gemini API key is not configured. "
                "Set GEMINI_API_KEY in environment or EmbeddingConfig.api_key."
            )

        genai.configure(api_key=api_key)
        self._configured = True

    def embed_text(self, text: str) -> list[float]:
        import google.generativeai as genai

        if not self._configured:
            raise EmbeddingFailureError("GeminiEmbedding not initialized. Call initialize() first.")
        if not text or not text.strip():
            raise EmbeddingFailureError("Cannot embed empty text.")

        try:
            result = genai.embed_content(
                model=self._model,
                content=text,
            )
            emb = result["embedding"]
            if isinstance(emb, list) and emb and isinstance(emb[0], (int, float)):
                return list(emb)
            return list(emb[0])
        except Exception as e:
            raise EmbeddingFailureError(f"Gemini embed_text failed: {e}") from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        import google.generativeai as genai

        if not self._configured:
            raise EmbeddingFailureError("GeminiEmbedding not initialized. Call initialize() first.")
        if not texts:
            return []
        if any(not t or not t.strip() for t in texts):
            raise EmbeddingFailureError("Cannot embed texts containing empty entries.")

        try:
            result = genai.embed_content(
                model=self._model,
                content=texts,
            )
            emb = result["embedding"]
            if isinstance(emb, list) and emb and isinstance(emb[0], list):
                return [list(v) for v in emb]
            return [list(emb)]
        except Exception as e:
            raise EmbeddingFailureError(f"Gemini embed_batch failed: {e}") from e

    def embed_query(self, text: str) -> list[float]:
        return self.embed_text(text)

    def dimension(self) -> int:
        dimensions = {
            "text-embedding-004": 768,
            "text-embedding-005": 768,
            "text-embedding-001": 768,
            "text-multilingual-embedding-002": 768,
            "text-embedding-preview-0409": 768,
            "text-embedding-gecko": 768,
            "text-embedding-gecko-multilingual": 768,
        }
        return dimensions.get(self._model, 768)

    def model_name(self) -> str:
        return self._model

    def provider_name(self) -> str:
        return "gemini"

    def health_check(self) -> dict:
        if not self._configured:
            return {"status": "error", "error": "Not initialized"}
        try:
            self.embed_text("health check")
            return {"status": "ok", "error": None}
        except Exception as e:
            return {"status": "error", "error": str(e)}


EmbeddingRegistry.register("gemini", GeminiEmbedding)
