from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from app.core.prompt_loader import PROMPTS_DIR
from app.core.prompt_loader import PromptLoader as CorePromptLoader
from app.prompts.loader import RAGPrompt, RAGPromptLoader


class PromptManager:
    """Central registry for managing all RAG prompts.

    Provides:
    - Category-based prompt discovery
    - Version-aware loading with caching
    - Metadata querying
    - Bulk preloading
    """

    def __init__(self, loader: Optional[RAGPromptLoader] = None):
        self._loader = loader or RAGPromptLoader()

    def get_prompt(self, path: str) -> RAGPrompt:
        return self._loader.load(path)

    def render(self, path: str, **variables: Any) -> str:
        prompt = self.get_prompt(path)
        return prompt.render(**variables)

    def get_version(self, path: str) -> Optional[str]:
        version = self._loader.get_version(path)
        return str(version) if version else None

    def list_categories(self) -> list[str]:
        categories: set[str] = set()
        for subdir in PROMPTS_DIR.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("_"):
                categories.add(subdir.name)
        return sorted(categories)

    def list_prompts(self, category: Optional[str] = None) -> list[dict[str, Any]]:
        if category:
            search_path = PROMPTS_DIR / category
            if not search_path.is_dir():
                return []
            pattern = "*.md"
        else:
            search_path = PROMPTS_DIR
            pattern = "**/*.md"

        result: list[dict[str, Any]] = []
        for md_file in sorted(search_path.glob(pattern)):
            relative = md_file.relative_to(PROMPTS_DIR)
            path_key = str(relative.with_suffix("")).replace("\\", "/")
            try:
                prompt = self._loader.load(path_key)
                result.append({
                    "path": path_key,
                    "category": prompt.category,
                    "name": prompt.name,
                    "version": str(prompt.version),
                    "purpose": prompt.metadata.get("purpose", ""),
                    "last_updated": prompt.metadata.get("last_updated", ""),
                    "author": prompt.metadata.get("author", ""),
                    "input_variables": [
                        v["name"] for v in prompt.metadata.get("input_variables", [])
                    ],
                })
            except (FileNotFoundError, ValueError):
                continue

        return result

    def get_prompt_metadata(self, path: str) -> dict[str, Any]:
        prompt = self.get_prompt(path)
        return {
            "path": prompt.path_key,
            "category": prompt.category,
            "name": prompt.name,
            "version": str(prompt.version),
            "content_hash": prompt.version.content_hash,
            **prompt.metadata,
        }

    def preload_all(self) -> int:
        count = 0
        for md_file in PROMPTS_DIR.rglob("*.md"):
            relative = md_file.relative_to(PROMPTS_DIR)
            path_key = str(relative.with_suffix("")).replace("\\", "/")
            try:
                self._loader.load(path_key)
                count += 1
            except (FileNotFoundError, ValueError):
                continue
        return count

    def invalidate_cache(self, path: Optional[str] = None) -> None:
        if path:
            self._loader.invalidate(path)
        else:
            self._loader.clear_cache()
