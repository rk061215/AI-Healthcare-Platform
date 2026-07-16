import pytest
from app.validation.optimization.chunk_optimizer import ChunkOptimizer, ChunkConfig
from app.validation.optimization.retrieval_optimizer import RetrievalOptimizer, RetrievalConfig
from app.validation.optimization.prompt_optimizer import PromptOptimizer, PromptVariant
from app.validation.optimization.reranking_optimizer import RerankingOptimizer, RerankingConfig


class TestChunkOptimizer:
    def test_suggest_sizes(self):
        opt = ChunkOptimizer()
        configs = opt.suggest_sizes(min_size=256, max_size=512, step=256, overlaps=[0, 64])
        assert len(configs) == 4

    def test_suggest_strategies(self):
        opt = ChunkOptimizer()
        configs = opt.suggest_strategies()
        assert len(configs) > 0

    def test_record_and_best(self):
        opt = ChunkOptimizer()
        c1 = ChunkConfig(chunk_size=256, chunk_overlap=0)
        c2 = ChunkConfig(chunk_size=512, chunk_overlap=64)
        opt.record_trial(c1, {"recall": 0.7, "f1": 0.6})
        opt.record_trial(c2, {"recall": 0.9, "f1": 0.85})
        best = opt.best_config()
        assert best is not None
        assert best.chunk_size == 512

    def test_top_n(self):
        opt = ChunkOptimizer()
        for i in range(10):
            opt.record_trial(ChunkConfig(chunk_size=100 + i * 10), {"recall": i / 10})
        top = opt.top_n(3)
        assert len(top) == 3
        assert top[0].score >= top[1].score

    def test_summary_empty(self):
        opt = ChunkOptimizer()
        s = opt.summary()
        assert s["trials"] == 0

    def test_summary(self):
        opt = ChunkOptimizer()
        opt.record_trial(ChunkConfig(chunk_size=512), {"recall": 0.8, "f1": 0.75})
        s = opt.summary()
        assert s["trials"] == 1
        assert s["best"]["chunk_size"] == 512


class TestRetrievalOptimizer:
    def test_suggest_configs(self):
        opt = RetrievalOptimizer()
        configs = opt.suggest_configs()
        assert len(configs) > 0

    def test_record_and_best(self):
        opt = RetrievalOptimizer()
        c1 = RetrievalConfig(top_k=3, similarity_threshold=0.7)
        c2 = RetrievalConfig(top_k=10, similarity_threshold=0.6)
        opt.record_trial(c1, {"recall_at_5": 0.6, "precision_at_5": 0.7})
        opt.record_trial(c2, {"recall_at_5": 0.9, "precision_at_5": 0.8})
        best = opt.best_config()
        assert best is not None
        assert best.top_k == 10

    def test_summary(self):
        opt = RetrievalOptimizer()
        c = RetrievalConfig(top_k=5)
        opt.record_trial(c, {"recall_at_5": 0.8, "precision_at_5": 0.7})
        s = opt.summary()
        assert s["trials"] == 1
        assert s["best"]["top_k"] == 5


class TestPromptOptimizer:
    def test_register_variant(self):
        opt = PromptOptimizer()
        v = PromptVariant(name="concise", template="Answer concisely: {query}")
        opt.register_variant(v)
        assert "concise" in opt.variants

    def test_remove_variant(self):
        opt = PromptOptimizer()
        opt.register_variant(PromptVariant(name="v1", template="t1"))
        assert opt.remove_variant("v1") is True
        assert opt.remove_variant("nonexistent") is False

    def test_get_variant(self):
        opt = PromptOptimizer()
        v = PromptVariant(name="v1", template="t1")
        opt.register_variant(v)
        assert opt.get_variant("v1") is v
        assert opt.get_variant("missing") is None

    def test_record_trial(self):
        opt = PromptOptimizer()
        opt.register_variant(PromptVariant(name="v1", template="t1"))
        trial = opt.record_trial("v1", {"answer_relevance": 0.9, "groundedness": 0.85, "hallucination_rate": 0.05})
        assert trial is not None
        assert trial.score > 0

    def test_record_trial_missing_variant(self):
        opt = PromptOptimizer()
        assert opt.record_trial("missing", {}) is None

    def test_best_variant(self):
        opt = PromptOptimizer()
        opt.register_variant(PromptVariant(name="good", template="g", temperature=0.3))
        opt.register_variant(PromptVariant(name="better", template="b", temperature=0.5))
        opt.record_trial("good", {"answer_relevance": 0.7, "groundedness": 0.7, "hallucination_rate": 0.1})
        opt.record_trial("better", {"answer_relevance": 0.9, "groundedness": 0.9, "hallucination_rate": 0.02})
        best = opt.best_variant()
        assert best is not None
        assert best.name == "better"

    def test_summary(self):
        opt = PromptOptimizer()
        opt.register_variant(PromptVariant(name="v1", template="t1"))
        opt.record_trial("v1", {"answer_relevance": 0.8, "groundedness": 0.8, "hallucination_rate": 0.1})
        s = opt.summary()
        assert s["variants_registered"] == 1
        assert s["trials"] == 1


class TestRerankingOptimizer:
    def test_suggest_configs(self):
        opt = RerankingOptimizer()
        configs = opt.suggest_configs()
        assert len(configs) > 0

    def test_record_and_best(self):
        opt = RerankingOptimizer()
        c1 = RerankingConfig(strategy="score", final_k=5)
        c2 = RerankingConfig(strategy="diversity", final_k=5, diversity_penalty=0.3)
        opt.record_trial(c1, {"ndcg": 0.7, "mrr": 0.6})
        opt.record_trial(c2, {"ndcg": 0.9, "mrr": 0.85})
        best = opt.best_config()
        assert best is not None
        assert best.strategy == "diversity"

    def test_top_n(self):
        opt = RerankingOptimizer()
        for i in range(5):
            opt.record_trial(RerankingConfig(strategy=f"s{i}"), {"ndcg": i / 10, "mrr": i / 10})
        top = opt.top_n(2)
        assert len(top) == 2

    def test_summary(self):
        opt = RerankingOptimizer()
        opt.record_trial(RerankingConfig(strategy="score"), {"ndcg": 0.8, "mrr": 0.7})
        s = opt.summary()
        assert s["trials"] == 1
        assert s["best"]["strategy"] == "score"
