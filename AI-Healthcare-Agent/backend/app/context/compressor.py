from __future__ import annotations

from typing import Optional

from app.context.config import ContextConfig
from app.context.exceptions import CompressionError
from app.context.models import CitationInfo, ContextFragment


class Compressor:
    """Merges overlapping or adjacent context fragments."""

    def __init__(self, config: Optional[ContextConfig] = None) -> None:
        self._config = config or ContextConfig()

    def compress(
        self, fragments: list[ContextFragment]
    ) -> tuple[list[ContextFragment], int]:
        if not fragments:
            return [], 0

        merged_result: list[ContextFragment] = []
        total_merged = 0

        for frag in fragments:
            if not merged_result:
                merged_result.append(frag)
                continue

            last = merged_result[-1]
            merged_frag = self._try_merge(last, frag)
            if merged_frag is not None:
                merged_result[-1] = merged_frag
                total_merged += 1
            else:
                merged_result.append(frag)

        return merged_result, total_merged

    def _try_merge(
        self, a: ContextFragment, b: ContextFragment
    ) -> Optional[ContextFragment]:
        if not self._is_adjacent_or_overlapping(a, b):
            return None

        if a.citation.report_id != b.citation.report_id:
            return None

        merged = ContextFragment(
            text=a.text + "\n" + b.text,
            score=max(a.score, b.score),
            citation=a.citation,
            original_chunk_index=a.original_chunk_index,
            rank=a.rank,
            merged=True,
            source_fragment_ids=a.source_fragment_ids
            + [b.citation.chunk_id],
        )
        return merged

    def _is_adjacent_or_overlapping(
        self, a: ContextFragment, b: ContextFragment
    ) -> bool:
        if a.citation.section != b.citation.section:
            return False

        if a.citation.report_id != b.citation.report_id:
            return False

        diff = abs(a.original_chunk_index - b.original_chunk_index)
        if diff <= 1:
            return True

        overlap = self._compute_text_overlap(a.text, b.text)
        return overlap >= self._config.overlap_threshold_chars

    def _compute_text_overlap(self, text_a: str, text_b: str) -> int:
        if len(text_a) < 10 or len(text_b) < 10:
            return 0

        tail = text_a[-self._config.overlap_threshold_chars * 2 :].lower()
        head = text_b[: self._config.overlap_threshold_chars * 2].lower()

        for size in range(min(100, len(tail), len(head)), 5, -1):
            for start in range(len(tail) - size + 1):
                substr = tail[start : start + size]
                if substr in head:
                    return size
        return 0
