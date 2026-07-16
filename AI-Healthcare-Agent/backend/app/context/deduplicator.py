from __future__ import annotations

from typing import Optional

from app.context.config import ContextConfig
from app.context.exceptions import DeduplicationError
from app.context.models import ContextFragment


class Deduplicator:
    """Removes duplicate context fragments based on text similarity.

    Uses exact text matching and configurable overlap detection.
    """

    def __init__(self, config: Optional[ContextConfig] = None) -> None:
        self._config = config or ContextConfig()

    def deduplicate(
        self, fragments: list[ContextFragment]
    ) -> tuple[list[ContextFragment], int]:
        if not fragments:
            return [], 0

        seen_texts: set[str] = set()
        seen_ids: set[str] = set()
        deduped: list[ContextFragment] = []
        removed = 0

        for frag in fragments:
            normalized = frag.text.strip().lower()
            chunk_id = frag.citation.chunk_id

            if chunk_id in seen_ids:
                removed += 1
                continue

            if normalized in seen_texts:
                removed += 1
                continue

            if self._is_overlap_duplicate(normalized, seen_texts):
                removed += 1
                continue

            seen_texts.add(normalized)
            seen_ids.add(chunk_id)
            deduped.append(frag)

        return deduped, removed

    def _is_overlap_duplicate(
        self, text: str, seen_texts: set[str], threshold: Optional[int] = None
    ) -> bool:
        if threshold is None:
            threshold = self._config.overlap_threshold_chars

        if threshold <= 0:
            return False

        for seen in seen_texts:
            overlap = self._compute_overlap(text, seen)
            if overlap >= threshold:
                return True
        return False

    def _compute_overlap(self, a: str, b: str) -> int:
        if len(a) < 10 or len(b) < 10:
            return 0

        shorter = a if len(a) < len(b) else b
        longer = b if len(a) < len(b) else a

        for size in range(min(50, len(shorter)), 5, -1):
            for start in range(len(shorter) - size + 1):
                substr = shorter[start : start + size]
                if substr in longer:
                    return size
        return 0
