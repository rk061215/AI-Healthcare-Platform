"""Reciprocal Rank Fusion and other result fusion strategies."""

from __future__ import annotations

from typing import Optional

from app.retrieval.models import RetrievalResult


def reciprocal_rank_fusion(
    result_lists: list[list[RetrievalResult]],
    k: int = 60,
    top_n: Optional[int] = None,
) -> list[RetrievalResult]:
    """Fuse multiple ranked result lists using Reciprocal Rank Fusion.

    Args:
        result_lists: Multiple ranked lists of RetrievalResult.
        k: RRF constant (default 60).
        top_n: Maximum number of results to return.

    Returns:
        Fused and re-ranked list of RetrievalResult.
    """
    scores: dict[str, tuple[float, RetrievalResult]] = {}

    for rank_list in result_lists:
        for rank, result in enumerate(rank_list):
            rrf_score = 1.0 / (k + rank + 1)
            if result.chunk_id in scores:
                existing_score, existing = scores[result.chunk_id]
                scores[result.chunk_id] = (existing_score + rrf_score, existing)
            else:
                scores[result.chunk_id] = (rrf_score, result)

    sorted_results = sorted(
        scores.values(),
        key=lambda x: x[0],
        reverse=True,
    )

    fused = [
        RetrievalResult(
            chunk_id=r.chunk_id,
            text=r.text,
            score=round(s, 6),
            document_id=r.document_id,
            report_id=r.report_id,
            patient_id=r.patient_id,
            document_type=r.document_type,
            section=r.section,
            page=r.page,
            chunk_index=r.chunk_index,
            source=r.source,
            language=r.language,
            metadata={**r.metadata, "fusion_score": s},
        )
        for s, r in sorted_results
    ]

    if top_n is not None:
        fused = fused[:top_n]

    return fused
