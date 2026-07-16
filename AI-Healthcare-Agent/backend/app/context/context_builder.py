from __future__ import annotations

import time
from typing import Optional

from app.context.citation import CitationGenerator
from app.context.compressor import Compressor
from app.context.config import ContextConfig
from app.context.deduplicator import Deduplicator
from app.context.exceptions import EmptyContextError
from app.context.models import (
    BuildContextInput,
    BuildContextResult,
    CitationInfo,
    ContextFragment,
    TokenUsageInfo,
)
from app.context.ranker import Ranker
from app.context.token_budget import TokenBudgetManager, estimate_tokens
from app.retrieval.models import RetrievedDocument


class ContextBuilder:
    """Builds optimized LLM-ready context from retrieved documents.

    Pipeline:
    1. Convert RetrievedDocument → ContextFragments
    2. Deduplicate fragments
    3. Rank by relevance and medical priority
    4. Compress/merge overlapping fragments
    5. Apply token budget
    6. Generate citations
    7. Assemble final context string
    """

    def __init__(self, config: Optional[ContextConfig] = None) -> None:
        self._config = config or ContextConfig()
        self._deduplicator = Deduplicator(config=self._config)
        self._ranker = Ranker(config=self._config)
        self._compressor = Compressor(config=self._config)
        self._token_budget = TokenBudgetManager(config=self._config)
        self._citation_gen = CitationGenerator(
            include_citations=self._config.enable_citations
        )

    def build(
        self,
        retrieved: RetrievedDocument,
        max_tokens: Optional[int] = None,
        strategy: Optional[str] = None,
    ) -> BuildContextResult:
        if not retrieved.results:
            return self._empty_result()

        fragments = self._to_fragments(retrieved)
        total_input = len(fragments)

        budget = max_tokens or self._config.max_tokens

        pipeline_start = time.perf_counter()

        if self._config.enable_dedup:
            fragments, dedup_removed = self._deduplicator.deduplicate(fragments)
        else:
            dedup_removed = 0
        after_dedup = len(fragments)

        if self._config.enable_ranking:
            fragments = self._ranker.rank(fragments)
        after_rank = len(fragments)

        if self._config.enable_compression:
            fragments, compressed_merged = self._compressor.compress(fragments)
        else:
            compressed_merged = 0
        after_compress = len(fragments)

        original_strategy = self._config.strategy
        if strategy:
            self._config.strategy = strategy

        fragments, token_usage = self._token_budget.enforce_budget(
            fragments, max_tokens=budget
        )

        if strategy:
            self._config.strategy = original_strategy

        fragments_in_context = len(fragments)

        citations = self._citation_gen.extract_citations(fragments)

        context_parts = []
        for i, frag in enumerate(fragments):
            annotated = self._citation_gen.annotate_fragment(frag, i + 1)
            context_parts.append(annotated)

        context_str = "\n\n".join(context_parts)

        citation_block = self._citation_gen.format_citation_block(citations)
        if citation_block:
            context_str += citation_block

        elapsed = (time.perf_counter() - pipeline_start) * 1000

        return BuildContextResult(
            context=context_str,
            fragments=fragments,
            token_usage=token_usage,
            citations=citations,
            total_fragments_input=total_input,
            fragments_after_dedup=after_dedup,
            fragments_after_rank=after_rank,
            fragments_after_compress=after_compress,
            fragments_in_context=fragments_in_context,
            dedup_removed=dedup_removed,
            compressed_merged=compressed_merged,
            truncated=token_usage.truncated,
            build_time_ms=round(elapsed, 2),
        )

    def build_from_fragments(
        self,
        fragments: list[ContextFragment],
        query: str = "",
        max_tokens: Optional[int] = None,
    ) -> BuildContextResult:
        if not fragments:
            return self._empty_result()

        total_input = len(fragments)
        budget = max_tokens or self._config.max_tokens

        pipeline_start = time.perf_counter()

        if self._config.enable_dedup:
            fragments, dedup_removed = self._deduplicator.deduplicate(fragments)
        else:
            dedup_removed = 0
        after_dedup = len(fragments)

        if self._config.enable_ranking:
            fragments = self._ranker.rank(fragments)
        after_rank = len(fragments)

        if self._config.enable_compression:
            fragments, compressed_merged = self._compressor.compress(fragments)
        else:
            compressed_merged = 0
        after_compress = len(fragments)

        fragments, token_usage = self._token_budget.enforce_budget(
            fragments, max_tokens=budget
        )

        fragments_in_context = len(fragments)
        citations = self._citation_gen.extract_citations(fragments)

        context_parts = []
        for i, frag in enumerate(fragments):
            annotated = self._citation_gen.annotate_fragment(frag, i + 1)
            context_parts.append(annotated)

        context_str = "\n\n".join(context_parts)
        citation_block = self._citation_gen.format_citation_block(citations)
        if citation_block:
            context_str += citation_block

        elapsed = (time.perf_counter() - pipeline_start) * 1000

        return BuildContextResult(
            context=context_str,
            fragments=fragments,
            token_usage=token_usage,
            citations=citations,
            total_fragments_input=total_input,
            fragments_after_dedup=after_dedup,
            fragments_after_rank=after_rank,
            fragments_after_compress=after_compress,
            fragments_in_context=fragments_in_context,
            dedup_removed=dedup_removed,
            compressed_merged=compressed_merged,
            truncated=token_usage.truncated,
            build_time_ms=round(elapsed, 2),
        )

    def _to_fragments(
        self, retrieved: RetrievedDocument
    ) -> list[ContextFragment]:
        fragments = []
        for i, result in enumerate(retrieved.results):
            citation = CitationInfo(
                document_id=result.document_id,
                report_id=result.report_id,
                chunk_id=result.chunk_id,
                page=result.page,
                section=result.section,
                chunk_index=result.chunk_index,
                source=result.source,
            )
            fragments.append(
                ContextFragment(
                    text=result.text,
                    score=result.score,
                    citation=citation,
                    original_chunk_index=result.chunk_index,
                    rank=0,
                )
            )
        return fragments

    def _empty_result(self) -> BuildContextResult:
        return BuildContextResult(
            context="",
            fragments=[],
            token_usage=TokenUsageInfo(),
            citations=[],
            total_fragments_input=0,
            fragments_after_dedup=0,
            fragments_after_rank=0,
            fragments_after_compress=0,
            fragments_in_context=0,
            dedup_removed=0,
            compressed_merged=0,
            truncated=False,
            build_time_ms=0.0,
        )

    @property
    def config(self) -> ContextConfig:
        return self._config
