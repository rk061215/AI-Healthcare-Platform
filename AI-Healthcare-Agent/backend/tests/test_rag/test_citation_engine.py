from app.rag.citation_engine import CitationEngine
from app.rag.models import CitationBlock, CitationEntry, RAGContext


class TestCitationEngine:
    def setup_method(self):
        self.engine = CitationEngine()

    def test_analyze_citations_empty(self):
        analysis = self.engine.analyze_citations(CitationBlock())
        assert analysis.total_citations == 0

    def test_analyze_citations_with_entries(self):
        block = CitationBlock(citations=[
            CitationEntry(citation_id=1, document_id="doc1", chunk_id="chunk1", score=0.9),
            CitationEntry(citation_id=2, document_id="doc2", chunk_id="chunk2", score=0.7),
        ])
        analysis = self.engine.analyze_citations(block)
        assert analysis.total_citations == 2
        assert analysis.average_relevance > 0

    def test_extract_inline_citations(self):
        refs = self.engine.extract_inline_citations(
            "The patient has diabetes [citation:1] and takes metformin [citation:2]"
        )
        assert len(refs) == 2
        assert refs[0]["citation_id"] == 1
        assert refs[1]["citation_id"] == 2

    def test_no_inline_citations(self):
        refs = self.engine.extract_inline_citations("The patient has diabetes")
        assert refs == []

    def test_claim_citation_map(self):
        mapping = self.engine.get_claim_citation_map(
            "Patient has diabetes [citation:1]. Takes metformin [citation:2].",
            CitationBlock(),
        )
        assert len(mapping) >= 1
