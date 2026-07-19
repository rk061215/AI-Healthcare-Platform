from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.models import RetrievalResult


def _make_result(chunk_id: str, score: float) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        text=f"Document {chunk_id}",
        score=score,
    )


class TestReciprocalRankFusion:
    def test_empty_input(self):
        assert reciprocal_rank_fusion([]) == []

    def test_single_list(self):
        results = [_make_result("a", 0.9), _make_result("b", 0.8)]
        fused = reciprocal_rank_fusion([results])
        assert len(fused) == 2

    def test_fuses_two_lists(self):
        list1 = [_make_result("a", 0.9), _make_result("b", 0.8)]
        list2 = [_make_result("b", 0.7), _make_result("c", 0.6)]
        fused = reciprocal_rank_fusion([list1, list2])
        assert len(fused) >= 2
        ids = [r.chunk_id for r in fused]
        assert "a" in ids
        assert "b" in ids
        assert "c" in ids

    def test_shared_document_gets_higher_score(self):
        list1 = [_make_result("a", 0.9), _make_result("b", 0.8)]
        list2 = [_make_result("a", 0.7), _make_result("b", 0.6)]
        fused = reciprocal_rank_fusion([list1, list2])
        assert fused[0].chunk_id == "a"

    def test_top_n_limits_results(self):
        results = [_make_result(f"doc{i}", 1.0) for i in range(10)]
        fused = reciprocal_rank_fusion([results], top_n=3)
        assert len(fused) == 3

    def test_fusion_score_in_metadata(self):
        list1 = [_make_result("a", 0.9)]
        list2 = [_make_result("a", 0.8)]
        fused = reciprocal_rank_fusion([list1, list2])
        assert "fusion_score" in fused[0].metadata
