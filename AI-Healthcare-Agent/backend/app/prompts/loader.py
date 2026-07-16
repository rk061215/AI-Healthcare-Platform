from __future__ import annotations

import hashlib
from typing import Any, Optional

from app.core.prompt_loader import Prompt as CorePrompt
from app.core.prompt_loader import PromptLoader as CorePromptLoader
from app.prompts.cache import PromptCache


class PromptVersion:
    """Semantic version metadata for a prompt template."""

    def __init__(self, version_string: str, content_hash: str, metadata: dict[str, Any]):
        self.version_string = version_string
        self.content_hash = content_hash
        self.metadata = metadata

    @property
    def major(self) -> int:
        parts = self.version_string.split(".")
        try:
            return int(parts[0])
        except (IndexError, ValueError):
            return 0

    @property
    def minor(self) -> int:
        parts = self.version_string.split(".")
        try:
            return int(parts[1]) if len(parts) > 1 else 0
        except ValueError:
            return 0

    @property
    def patch(self) -> int:
        parts = self.version_string.split(".")
        try:
            return int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            return 0

    def __str__(self) -> str:
        return self.version_string

    def __repr__(self) -> str:
        return f"PromptVersion({self.version_string}, hash={self.content_hash[:8]}...)"


class RAGPrompt:
    """A prompt loaded with version tracking for RAG use."""

    def __init__(self, core_prompt: CorePrompt):
        self._core = core_prompt
        self.category = core_prompt.category
        self.name = core_prompt.name
        self.metadata = core_prompt.metadata
        self.content = core_prompt.content

        raw_version = self.metadata.get("prompt_version", "0.0.0")
        content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        self.version = PromptVersion(
            version_string=str(raw_version),
            content_hash=content_hash,
            metadata=self.metadata,
        )

    def render(self, **kwargs: Any) -> str:
        return self._core.render(**kwargs)

    @property
    def path_key(self) -> str:
        return f"{self.category}/{self.name}" if self.category else self.name

    def __repr__(self) -> str:
        return f"RAGPrompt({self.path_key}, v{self.version})"


class RAGPromptLoader:
    """Loads and caches prompts with version tracking for the RAG system.

    Wraps the existing PromptLoader (app.core.prompt_loader) and adds
    version awareness, hashing, and dedicated TTL+LRU caching.
    """

    def __init__(self, cache: Optional[PromptCache] = None):
        self._cache = cache or PromptCache()

    def load(self, path: str, bypass_cache: bool = False) -> RAGPrompt:
        if not bypass_cache:
            cached = self._cache.get(path)
            if cached is not None:
                return cached

        core_prompt = CorePromptLoader.load(path, use_cache=False)
        rag_prompt = RAGPrompt(core_prompt)
        self._cache.set(path, rag_prompt)
        return rag_prompt

    def get_version(self, path: str) -> Optional[PromptVersion]:
        try:
            prompt = self.load(path)
            return prompt.version
        except FileNotFoundError:
            return None

    def invalidate(self, path: str) -> None:
        self._cache.invalidate(path)

    def clear_cache(self) -> None:
        self._cache.clear()

    @property
    def cache_stats(self) -> dict:
        return self._cache.stats
