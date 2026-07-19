from app.rag.confidence_engine import ConfidenceEngine
from app.rag.models import CitationBlock, CitationEntry


class TestConfidenceEngine:
    def setup_method(self):
        self.engine = ConfidenceEngine()

    def test_evaluate_empty_response(self):
        result = self.engine.evaluate("", CitationBlock())
        assert result.overall_confidence == 0.0
        assert result.requires_human_review

    def test_evaluate_with_citations(self):
        citations = CitationBlock(citations=[
            CitationEntry(citation_id=1, document_id="doc1", chunk_id="chunk1", score=0.9, text_snippet="normal finding"),
        ])
        result = self.engine.evaluate(
            "The patient's lab results are normal [citation:1].",
            citations,
        )
        assert result.overall_confidence > 0

    def test_evaluate_with_hallucination(self):
        citations = CitationBlock(citations=[
            CitationEntry(citation_id=1, document_id="doc1", chunk_id="chunk1", score=0.9),
        ])
        result = self.engine.evaluate(
            "The patient has diabetes [citation:1] and takes metformin [citation:99].",
            citations,
        )
        assert result.breakdown.hallucination_risk > 0

    def test_confidence_label(self):
        assert self.engine.get_confidence_label(0.9) == "high"
        assert self.engine.get_confidence_label(0.6) == "medium"
        assert self.engine.get_confidence_label(0.3) == "low"

    def test_no_citations_low_confidence(self):
        result = self.engine.evaluate("The patient is healthy.", CitationBlock())
        assert result.overall_confidence < 0.5
