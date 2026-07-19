from app.retrieval.context_compressor import ContextCompressor
from app.retrieval.models import RetrievalResult


def _make_result(chunk_id: str, text: str, score: float = 0.5) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        text=text,
        score=score,
    )


class TestContextCompressor:
    def setup_method(self):
        self.compressor = ContextCompressor(max_tokens=1000)

    def test_compress_empty(self):
        assert self.compressor.compress("query", []) == []

    def test_deduplicates_duplicates(self):
        results = [
            _make_result("a", "Same text here for testing purposes", 0.9),
            _make_result("b", "Same text here for testing purposes", 0.8),
        ]
        compressed = self.compressor.compress("query", results)
        assert len(compressed) <= 1

    def test_different_docs_kept(self):
        results = [
            _make_result("a", "Unique content one", 0.9),
            _make_result("b", "Different content two", 0.8),
        ]
        compressed = self.compressor.compress("query", results)
        assert len(compressed) == 2

    def test_trim_low_score(self):
        results = [
            _make_result("a", "High relevance doc", 0.9),
            _make_result("b", "Medium relevance doc", 0.5),
            _make_result("c", "Low relevance doc", 0.1),
        ]
        compressed = self.compressor.compress("query", results)
        assert len(compressed) < 3  # should trim low scores

    def test_compressed_metadata_flag(self):
        results = [_make_result("a", "Short doc", 0.9)]
        compressed = self.compressor.compress("query", results)
        assert len(compressed) > 0
        assert compressed[0].metadata.get("compressed")
