"""Dynamic prompt loader — loads prompt templates from Markdown files.

Usage:
    prompt = PromptLoader.load("medical/report_analysis")
    rendered = prompt.render(text=ocr_text)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt file cannot be found."""


class PromptParseError(ValueError):
    """Raised when a prompt file has invalid frontmatter."""


@dataclass
class Prompt:
    """A loaded prompt template with metadata and content."""

    category: str
    name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    content: str = ""
    file_path: Path | None = None

    def render(self, **kwargs: Any) -> str:
        """Render the prompt template by substituting variables.

        Supports both {{ variable }} (mustache-style) and {variable} syntax.
        Missing variables are replaced with empty string.
        """
        result = self.content
        for key, value in kwargs.items():
            result = result.replace("{{ " + key + " }}", str(value))
            result = result.replace("{{" + key + "}}", str(value))
            result = result.replace("{" + key + "}", str(value))
        result = re.sub(r"\{\{.*?\}\}", "", result)
        result = re.sub(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", "", result)
        return result


class PromptLoader:
    """Loads prompt templates from Markdown files with YAML frontmatter."""

    _cache: dict[str, Prompt] = {}

    @classmethod
    def load(cls, path: str, use_cache: bool = True) -> Prompt:
        """Load a prompt by its relative path (e.g. 'medical/report_analysis').

        Args:
            path: Relative path without extension (e.g. 'medical/report_analysis').
            use_cache: Whether to cache the loaded prompt in memory.

        Returns:
            Populated Prompt dataclass.

        Raises:
            PromptNotFoundError: If the file does not exist.
            PromptParseError: If frontmatter is malformed.
        """
        if use_cache and path in cls._cache:
            return cls._cache[path]

        file_path = PROMPTS_DIR / f"{path}.md"
        if not file_path.exists():
            raise PromptNotFoundError(f"Prompt not found: {path} (looked at {file_path})")

        content = file_path.read_text(encoding="utf-8")
        metadata, body = cls._parse_frontmatter(content)
        category = path.split("/")[0] if "/" in path else ""

        prompt = Prompt(
            category=category,
            name=file_path.stem,
            metadata=metadata,
            content=body.strip(),
            file_path=file_path,
        )

        if use_cache:
            cls._cache[path] = prompt

        return prompt

    @classmethod
    def load_all(cls, category: str | None = None) -> list[Prompt]:
        """Load all prompts, optionally filtered by category.

        Args:
            category: If provided, only load prompts from this subdirectory.

        Returns:
            List of Prompt dataclass instances.
        """
        if category:
            search_path = PROMPTS_DIR / category
            if not search_path.is_dir():
                return []
            pattern = "*.md"
        else:
            search_path = PROMPTS_DIR
            pattern = "**/*.md"

        prompts: list[Prompt] = []
        for md_file in sorted(search_path.glob(pattern)):
            relative = md_file.relative_to(PROMPTS_DIR)
            key = str(relative.with_suffix("")).replace("\\", "/")
            try:
                prompts.append(cls.load(key, use_cache=True))
            except (PromptNotFoundError, PromptParseError):
                continue

        return prompts

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the in-memory prompt cache."""
        cls._cache.clear()

    @classmethod
    def reload(cls, path: str) -> Prompt:
        """Force reload a prompt from disk, bypassing cache."""
        cls._cache.pop(path, None)
        return cls.load(path, use_cache=False)

    @classmethod
    def _parse_frontmatter(cls, content: str) -> tuple[dict[str, Any], str]:
        """Parse YAML frontmatter from Markdown content using PyYAML.

        Returns (metadata_dict, body_text). If no frontmatter, metadata is empty.
        """
        import yaml

        if not content.startswith("---"):
            return {}, content

        end_idx = content.find("---", 3)
        if end_idx == -1:
            raise PromptParseError("Unclosed frontmatter: expected closing '---'")

        frontmatter_text = content[3:end_idx].strip()
        body = content[end_idx + 3 :].strip()

        try:
            metadata = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            raise PromptParseError(f"Invalid YAML frontmatter: {e}") from e

        return metadata or {}, body

    @staticmethod
    def _coerce(value: str) -> Any:
        """Coerce string values to appropriate Python types."""
        if value.lower() in ("true", "yes"):
            return True
        if value.lower() in ("false", "no"):
            return False
        if value.lower() == "null":
            return None
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value
