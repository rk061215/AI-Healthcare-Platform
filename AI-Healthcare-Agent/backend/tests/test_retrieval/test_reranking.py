from app.retrieval.models import RetrievalResult
from app.retrieval.reranking import Reranker


def _make_result(chunk_id: str, text: str, score: float = 0.5) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        text=text,
        score=score,
    )


class TestReranker:
    def test_rerank_empty(self):
        reranker = Reranker()
        assert reranker.rerank("test", []) == []

    def test_rerank_fallback_scoring(self):
        reranker = Reranker()
        results = [
            _make_result("a", "metformin diabetes medication"),
            _make_result("b", "blood pressure hypertension"),
        ]
        reranked = reranker.rerank("diabetes medication", results)
        assert len(reranked) == 2

    def test_rerank_with_scores(self):
        reranker = Reranker()
        results = [_make_result("a", "test"), _make_result("b", "test")]
        reranked, scores = reranker.rerank_with_scores("test", results)
        assert len(reranked) == len(scores) == 2

    def test_top_k_limits(self):
        reranker = Reranker()
        results = [_make_result(f"doc{i}", "text") for i in range(10)]
        reranked = reranker.rerank("query", results, top_k=3)
        assert len(reranked) == 3
