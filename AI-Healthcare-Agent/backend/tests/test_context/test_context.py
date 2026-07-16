from __future__ import annotations

import pytest

from app.context import (
    CitationError,
    CitationGenerator,
    CompressionError,
    Compressor,
    ContextBuilder,
    ContextConfig,
    ContextError,
    ContextFragment,
    DeduplicationError,
    Deduplicator,
    EmptyContextError,
    RankingError,
    Ranker,
    TokenBudgetExceededError,
    TokenBudgetManager,
    TokenUsageInfo,
    BuildContextInput,
    BuildContextResult,
    CitationInfo,
    estimate_tokens,
)
from app.retrieval.models import RetrievalQuery, RetrievalResult, RetrievedDocument


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_fragments() -> list[ContextFragment]:
    return [
        ContextFragment(
            text="Patient has diabetes type 2",
            score=0.95,
            citation=CitationInfo(
                document_id="doc_1", report_id="R1", chunk_id="c1",
                section="diagnosis", chunk_index=0, source="ocr",
            ),
            original_chunk_index=0,
        ),
        ContextFragment(
            text="Prescribed Metformin 500mg",
            score=0.85,
            citation=CitationInfo(
                document_id="doc_1", report_id="R1", chunk_id="c2",
                section="medication", chunk_index=1, source="ocr",
            ),
            original_chunk_index=1,
        ),
        ContextFragment(
            text="Patient reports improved glucose levels",
            score=0.70,
            citation=CitationInfo(
                document_id="doc_1", report_id="R1", chunk_id="c3",
                section="assessment", chunk_index=2, source="ocr",
            ),
            original_chunk_index=2,
        ),
    ]


@pytest.fixture
def duplicate_fragments() -> list[ContextFragment]:
    text = "Patient has high blood pressure"
    return [
        ContextFragment(
            text=text,
            score=0.9,
            citation=CitationInfo(
                document_id="doc_1", report_id="R1", chunk_id="c1",
                section="diagnosis", chunk_index=0,
            ),
        ),
        ContextFragment(
            text=text,
            score=0.85,
            citation=CitationInfo(
                document_id="doc_1", report_id="R1", chunk_id="c2",
                section="diagnosis", chunk_index=1,
            ),
        ),
    ]


@pytest.fixture
def overlapping_fragments() -> list[ContextFragment]:
    return [
        ContextFragment(
            text="The patient was diagnosed with hypertension and prescribed Lisinopril 10mg daily. Follow up in 3 months.",
            score=0.9,
            citation=CitationInfo(
                document_id="doc_1", report_id="R1", chunk_id="c1",
                section="diagnosis", chunk_index=0,
            ),
            original_chunk_index=0,
        ),
        ContextFragment(
            text="Follow up in 3 months. Blood pressure should be monitored weekly.",
            score=0.8,
            citation=CitationInfo(
                document_id="doc_1", report_id="R1", chunk_id="c2",
                section="diagnosis", chunk_index=1,
            ),
            original_chunk_index=1,
        ),
    ]


@pytest.fixture
def sample_retrieved_doc() -> RetrievedDocument:
    results = [
        RetrievalResult(
            chunk_id="c1", text="Diabetes diagnosis", score=0.95,
            document_id="doc_1", report_id="R1", section="diagnosis",
            chunk_index=0, source="ocr", patient_id="P001",
        ),
        RetrievalResult(
            chunk_id="c2", text="Metformin prescription", score=0.85,
            document_id="doc_1", report_id="R1", section="medication",
            chunk_index=1, source="ocr", patient_id="P001",
        ),
    ]
    return RetrievedDocument(
        query=RetrievalQuery(text="diabetes"),
        results=results,
        total_results=2,
        returned_results=2,
        provider="vector_retriever",
    )


# =============================================================================
# Model Tests
# =============================================================================


class TestCitationInfo:
    def test_to_dict(self):
        c = CitationInfo(document_id="d1", report_id="R1", chunk_id="c1")
        d = c.to_dict()
        assert d["document_id"] == "d1"
        assert d["chunk_id"] == "c1"

    def test_to_dict_excludes_none(self):
        c = CitationInfo(document_id="d1", chunk_id="c1")
        d = c.to_dict()
        assert "report_id" not in d


class TestContextFragment:
    def test_defaults(self):
        f = ContextFragment(
            text="hello",
            score=0.9,
            citation=CitationInfo(document_id="d1", chunk_id="c1"),
        )
        assert f.merged is False
        assert f.source_fragment_ids == []
        assert f.rank == 0


class TestBuildContextResult:
    def test_defaults(self):
        r = BuildContextResult()
        assert r.context == ""
        assert r.fragments == []
        assert r.citations == []
        assert r.dedup_removed == 0


class TestTokenUsageInfo:
    def test_defaults(self):
        t = TokenUsageInfo()
        assert t.estimated_tokens == 0
        assert t.truncated is False


class TestBuildContextInput:
    def test_defaults(self):
        inp = BuildContextInput(query="test", fragments=[])
        assert inp.max_tokens == 4000
        assert inp.preserve_sections is True


# =============================================================================
# Token Budget Tests
# =============================================================================


class TestEstimateTokens:
    def test_short_text(self):
        assert estimate_tokens("hello") == 1

    def test_longer_text(self):
        text = "word " * 40
        tokens = estimate_tokens(text)
        assert tokens > 0

    def test_empty_text(self):
        assert estimate_tokens("") == 1


class TestTokenBudgetManager:
    def test_fixed_max(self):
        manager = TokenBudgetManager(ContextConfig(strategy="fixed_max"))
        fragments = [
            ContextFragment(text="A" * 100, score=0.9, citation=CitationInfo(document_id="d1", chunk_id=f"c{i}"))
            for i in range(10)
        ]
        selected, usage = manager.enforce_budget(fragments, max_tokens=50)
        assert len(selected) < 10 or usage.truncated
        assert usage.estimated_tokens <= 50

    def test_priority_truncation(self):
        config = ContextConfig(strategy="priority_truncation")
        manager = TokenBudgetManager(config)
        fragments = [
            ContextFragment(text="A" * 50, score=0.3, citation=CitationInfo(document_id="d1", chunk_id="c1", section="other")),
            ContextFragment(text="B" * 50, score=0.9, citation=CitationInfo(document_id="d1", chunk_id="c2", section="diagnosis")),
        ]
        selected, usage = manager.enforce_budget(fragments, max_tokens=100)
        assert len(selected) > 0

    def test_section_preserve(self):
        config = ContextConfig(strategy="section_preserve")
        manager = TokenBudgetManager(config)
        fragments = [
            ContextFragment(text="A" * 50, score=0.5, citation=CitationInfo(document_id="d1", chunk_id="c1", section="diagnosis")),
            ContextFragment(text="B" * 50, score=0.5, citation=CitationInfo(document_id="d1", chunk_id="c2", section="medication")),
        ]
        selected, usage = manager.enforce_budget(fragments, max_tokens=1000)
        assert len(selected) == 2

    def test_empty_fragments(self):
        manager = TokenBudgetManager()
        selected, usage = manager.enforce_budget([])
        assert selected == []
        assert usage.estimated_tokens == 0

    def test_no_truncation_when_within_budget(self):
        manager = TokenBudgetManager()
        fragments = [ContextFragment(text="short", score=0.9, citation=CitationInfo(document_id="d1", chunk_id="c1"))]
        selected, usage = manager.enforce_budget(fragments, max_tokens=1000)
        assert len(selected) == 1
        assert usage.truncated is False

    def test_unknown_strategy(self):
        manager = TokenBudgetManager(ContextConfig(strategy="invalid"))
        with pytest.raises(Exception):
            manager.enforce_budget(
                [ContextFragment(text="x", score=0.9, citation=CitationInfo(document_id="d1", chunk_id="c1"))],
                max_tokens=100,
            )


# =============================================================================
# Deduplicator Tests
# =============================================================================


class TestDeduplicator:
    def test_removes_exact_duplicates(self, duplicate_fragments):
        dedup = Deduplicator()
        result, removed = dedup.deduplicate(duplicate_fragments)
        assert len(result) == 1
        assert removed == 1

    def test_no_duplicates(self, sample_fragments):
        dedup = Deduplicator()
        result, removed = dedup.deduplicate(sample_fragments)
        assert len(result) == 3
        assert removed == 0

    def test_empty_input(self):
        dedup = Deduplicator()
        result, removed = dedup.deduplicate([])
        assert result == []
        assert removed == 0

    def test_removes_by_chunk_id(self):
        dedup = Deduplicator()
        fragments = [
            ContextFragment(text="unique text 1", score=0.9, citation=CitationInfo(document_id="d1", chunk_id="same_id")),
            ContextFragment(text="unique text 2", score=0.8, citation=CitationInfo(document_id="d1", chunk_id="same_id")),
        ]
        result, removed = dedup.deduplicate(fragments)
        assert len(result) == 1
        assert removed == 1


# =============================================================================
# Ranker Tests
# =============================================================================


class TestRanker:
    def test_ranks_by_score(self, sample_fragments):
        ranker = Ranker()
        ranked = ranker.rank(sample_fragments)
        assert ranked[0].score >= ranked[-1].score

    def test_priority_sections_first(self):
        ranker = Ranker()
        fragments = [
            ContextFragment(text="other", score=0.99, citation=CitationInfo(document_id="d1", chunk_id="c1", section="other")),
            ContextFragment(text="diagnosis", score=0.5, citation=CitationInfo(document_id="d1", chunk_id="c2", section="diagnosis")),
        ]
        ranked = ranker.rank(fragments)
        assert ranked[0].citation.section == "diagnosis"

    def test_empty_input(self):
        ranker = Ranker()
        assert ranker.rank([]) == []

    def test_sets_rank_field(self, sample_fragments):
        ranker = Ranker()
        ranked = ranker.rank(sample_fragments)
        for i, frag in enumerate(ranked):
            assert frag.rank == i + 1


# =============================================================================
# Compressor Tests
# =============================================================================


class TestCompressor:
    def test_merges_adjacent_fragments(self, overlapping_fragments):
        compressor = Compressor()
        result, merged = compressor.compress(overlapping_fragments)
        assert merged >= 1
        assert len(result) < len(overlapping_fragments) or merged > 0

    def test_no_merge_different_sections(self, sample_fragments):
        compressor = Compressor()
        result, merged = compressor.compress(sample_fragments)
        assert merged == 0
        assert len(result) == 3

    def test_empty_input(self):
        compressor = Compressor()
        result, merged = compressor.compress([])
        assert result == []
        assert merged == 0

    def test_merged_fragment_has_combined_text(self):
        compressor = Compressor()
        fragments = [
            ContextFragment(
                text="Part one.",
                score=0.9,
                citation=CitationInfo(document_id="d1", report_id="R1", chunk_id="c1", section="diagnosis", chunk_index=0),
                original_chunk_index=0,
            ),
            ContextFragment(
                text="Part two.",
                score=0.8,
                citation=CitationInfo(document_id="d1", report_id="R1", chunk_id="c2", section="diagnosis", chunk_index=1),
                original_chunk_index=1,
            ),
        ]
        result, merged = compressor.compress(fragments)
        assert merged == 1
        assert len(result) == 1
        assert "Part one." in result[0].text
        assert "Part two." in result[0].text
        assert result[0].merged is True

    def test_merged_tracks_source_ids(self):
        compressor = Compressor()
        fragments = [
            ContextFragment(text="A.", score=0.9, original_chunk_index=0,
                citation=CitationInfo(document_id="d1", report_id="R1", chunk_id="c1", section="diagnosis", chunk_index=0)),
            ContextFragment(text="B.", score=0.8, original_chunk_index=1,
                citation=CitationInfo(document_id="d1", report_id="R1", chunk_id="c2", section="diagnosis", chunk_index=1)),
        ]
        result, merged = compressor.compress(fragments)
        assert "c2" in result[0].source_fragment_ids


# =============================================================================
# CitationGenerator Tests
# =============================================================================


class TestCitationGenerator:
    def test_extract_citations(self, sample_fragments):
        gen = CitationGenerator()
        citations = gen.extract_citations(sample_fragments)
        assert len(citations) == 3

    def test_deduplicates_citations(self):
        gen = CitationGenerator()
        fragments = [
            ContextFragment(text="a", score=0.9, citation=CitationInfo(document_id="d1", chunk_id="c1")),
            ContextFragment(text="b", score=0.8, citation=CitationInfo(document_id="d1", chunk_id="c1")),
        ]
        citations = gen.extract_citations(fragments)
        assert len(citations) == 1

    def test_empty_fragments(self):
        gen = CitationGenerator()
        assert gen.extract_citations([]) == []

    def test_format_citation_block(self):
        gen = CitationGenerator()
        citations = [CitationInfo(document_id="d1", report_id="R1", section="diagnosis", page=3, source="ocr", chunk_id="c1")]
        block = gen.format_citation_block(citations)
        assert "d1" in block
        assert "R1" in block
        assert "diagnosis" in block
        assert "Page: 3" in block

    def test_format_empty_citations(self):
        gen = CitationGenerator()
        assert gen.format_citation_block([]) == ""

    def test_disable_citations(self):
        gen = CitationGenerator(include_citations=False)
        citations = [CitationInfo(document_id="d1", chunk_id="c1")]
        block = gen.format_citation_block(citations)
        assert block == ""

    def test_annotate_fragment(self):
        gen = CitationGenerator()
        frag = ContextFragment(
            text="test text",
            score=0.9,
            citation=CitationInfo(document_id="d1", section="diagnosis", page=2, chunk_id="c1"),
        )
        annotated = gen.annotate_fragment(frag, 1)
        assert "d1" in annotated
        assert "diagnosis" in annotated
        assert "p.2" in annotated
        assert "test text" in annotated


# =============================================================================
# ContextBuilder Tests
# =============================================================================


class TestContextBuilder:
    def test_build_from_retrieved(self, sample_retrieved_doc):
        builder = ContextBuilder()
        result = builder.build(sample_retrieved_doc)
        assert result.context != ""
        assert result.total_fragments_input == 2
        assert result.fragments_in_context <= 2
        assert len(result.citations) > 0
        assert result.build_time_ms > 0

    def test_build_from_fragments(self, sample_fragments):
        builder = ContextBuilder()
        result = builder.build_from_fragments(sample_fragments, query="diabetes")
        assert result.context != ""
        assert result.total_fragments_input == 3

    def test_empty_retrieved(self):
        builder = ContextBuilder()
        empty_doc = RetrievedDocument(query=RetrievalQuery(text="x"))
        result = builder.build(empty_doc)
        assert result.context == ""
        assert result.total_fragments_input == 0

    def test_empty_fragments(self):
        builder = ContextBuilder()
        result = builder.build_from_fragments([], query="test")
        assert result.context == ""

    def test_citations_included_in_context(self, sample_retrieved_doc):
        builder = ContextBuilder()
        result = builder.build(sample_retrieved_doc)
        assert "**Sources**" in result.context

    def test_citations_disabled(self, sample_retrieved_doc):
        config = ContextConfig(enable_citations=False)
        builder = ContextBuilder(config=config)
        result = builder.build(sample_retrieved_doc)
        assert "**Sources**" not in result.context

    def test_dedup_disabled(self, sample_retrieved_doc):
        config = ContextConfig(enable_dedup=False)
        builder = ContextBuilder(config=config)
        result = builder.build(sample_retrieved_doc)
        assert result.dedup_removed == 0

    def test_ranking_disabled(self, sample_retrieved_doc):
        config = ContextConfig(enable_ranking=False)
        builder = ContextBuilder(config=config)
        result = builder.build(sample_retrieved_doc)
        assert result.total_fragments_input > 0

    def test_compression_disabled(self, sample_retrieved_doc):
        config = ContextConfig(enable_compression=False)
        builder = ContextBuilder(config=config)
        result = builder.build(sample_retrieved_doc)
        assert result.compressed_merged == 0

    def test_token_budget_respected(self, sample_retrieved_doc):
        builder = ContextBuilder(ContextConfig(strategy="fixed_max"))
        result = builder.build(sample_retrieved_doc, max_tokens=5)
        assert result.token_usage.estimated_tokens <= 5 or result.truncated

    def test_pipeline_metrics(self, sample_retrieved_doc):
        builder = ContextBuilder()
        result = builder.build(sample_retrieved_doc)
        assert result.total_fragments_input > 0
        assert result.fragments_after_dedup > 0
        assert result.fragments_after_rank > 0
        assert result.fragments_after_compress > 0
        assert result.fragments_in_context > 0

    def test_config_property(self):
        config = ContextConfig(max_tokens=2000)
        builder = ContextBuilder(config=config)
        assert builder.config.max_tokens == 2000


# =============================================================================
# Exception Tests
# =============================================================================


class TestContextExceptions:
    def test_base(self):
        assert issubclass(ContextError, Exception)

    def test_empty_context(self):
        assert issubclass(EmptyContextError, ContextError)

    def test_citation_error(self):
        assert issubclass(CitationError, ContextError)

    def test_deduplication_error(self):
        assert issubclass(DeduplicationError, ContextError)

    def test_compression_error(self):
        assert issubclass(CompressionError, ContextError)

    def test_ranking_error(self):
        assert issubclass(RankingError, ContextError)

    def test_token_budget_exceeded(self):
        assert issubclass(TokenBudgetExceededError, ContextError)

    def test_configuration(self):
        from app.context.exceptions import ConfigurationError
        assert issubclass(ConfigurationError, ContextError)
