from __future__ import annotations

import time
from typing import Optional

from app.retrieval.models import RetrievalResult


class ContextCompressor:
    def __init__(
        self,
        max_tokens: int = 4000,
        compression_ratio: float = 0.7,
        min_chunk_tokens: int = 50,
    ):
        self._max_tokens = max_tokens
        self._compression_ratio = compression_ratio
        self._min_chunk_tokens = min_chunk_tokens

    def compress(
        self,
        query: str,
        results: list[RetrievalResult],
        max_tokens: Optional[int] = None,
    ) -> list[RetrievalResult]:
        if not results:
            return []

        start = time.perf_counter()
        max_tokens = max_tokens or self._max_tokens

        deduped = self._deduplicate(results)
        scored_and_trimmed = self._trim_low_score(deduped)
        truncated = self._truncate_to_budget(scored_and_trimmed, max_tokens)

        elapsed = (time.perf_counter() - start) * 1000
        for r in truncated:
            r.metadata["compress_time_ms"] = round(elapsed, 2)
            r.metadata["compressed"] = True

        return truncated

    def _deduplicate(
        self, results: list[RetrievalResult]
    ) -> list[RetrievalResult]:
        seen_texts: set[int] = set()
        deduped: list[RetrievalResult] = []

        for r in results:
            text_hash = hash(r.text[:200])
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                deduped.append(r)

        return deduped

    def _trim_low_score(
        self, results: list[RetrievalResult]
    ) -> list[RetrievalResult]:
        if not results:
            return results

        max_score = max(r.score for r in results)
        if max_score <= 0:
            return results

        threshold = max_score * (1.0 - self._compression_ratio)
        trimmed = [r for r in results if r.score >= threshold]

        return trimmed or results[:max(len(results) // 2, 1)]

    def _truncate_to_budget(
        self,
        results: list[RetrievalResult],
        max_tokens: int,
    ) -> list[RetrievalResult]:
        total = 0
        compressed: list[RetrievalResult] = []

        for r in results:
            doc_tokens = self._estimate_tokens(r.text)
            if total + doc_tokens <= max_tokens:
                compressed.append(r)
                total += doc_tokens
            else:
                allowed_chars = int((max_tokens - total) * 4)
                if allowed_chars > self._min_chunk_tokens * 4:
                    truncated_text = r.text[:allowed_chars]
                    compressed.append(RetrievalResult(
                        chunk_id=r.chunk_id,
                        text=truncated_text,
                        score=r.score,
                        document_id=r.document_id,
                        report_id=r.report_id,
                        patient_id=r.patient_id,
                        document_type=r.document_type,
                        section=r.section,
                        page=r.page,
                        chunk_index=r.chunk_index,
                        source=r.source,
                        language=r.language,
                        metadata={**r.metadata, "truncated": True},
                    ))
                break

        return compressed

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4 + 1
