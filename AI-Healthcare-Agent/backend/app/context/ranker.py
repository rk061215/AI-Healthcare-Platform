from __future__ import annotations

from typing import Optional

from app.context.config import ContextConfig
from app.context.exceptions import RankingError
from app.context.models import ContextFragment


class Ranker:
    """Ranks context fragments by relevance score and medical priority."""

    def __init__(self, config: Optional[ContextConfig] = None) -> None:
        self._config = config or ContextConfig()

    def rank(
        self, fragments: list[ContextFragment]
    ) -> list[ContextFragment]:
        if not fragments:
            return []

        priority_sections = list(self._config.priority_sections)

        def sort_key(f: ContextFragment) -> tuple[int, float, int]:
            section = f.citation.section or ""
            if section in priority_sections:
                priority = priority_sections.index(section)
            else:
                priority = len(priority_sections)
            return (priority, -f.score, f.original_chunk_index)

        ranked = sorted(fragments, key=sort_key)
        for i, frag in enumerate(ranked):
            frag.rank = i + 1
        return ranked
