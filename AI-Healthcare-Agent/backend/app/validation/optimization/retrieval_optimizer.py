from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RetrievalConfig:
    top_k: int = 5
    similarity_threshold: float = 0.7
    rerank: bool = False
    hybrid_search: bool = False
    use_mmr: bool = False
    mmr_lambda: float = 0.5
    diversity_factor: float = 0.3


@dataclass
class RetrievalTrial:
    config: RetrievalConfig
    metrics: dict[str, float] = field(default_factory=dict)
    score: float = 0.0


class RetrievalOptimizer:
    def __init__(self):
        self._trials: list[RetrievalTrial] = []

    @property
    def trials(self) -> list[RetrievalTrial]:
        return list(self._trials)

    def suggest_configs(self) -> list[RetrievalConfig]:
        configs: list[RetrievalConfig] = []
        for top_k in [3, 5, 10, 20]:
            for threshold in [0.5, 0.6, 0.7, 0.8]:
                configs.append(RetrievalConfig(top_k=top_k, similarity_threshold=threshold))
        for rerank in [True, False]:
            configs.append(RetrievalConfig(top_k=5, similarity_threshold=0.7, rerank=rerank))
        for use_mmr in [True, False]:
            configs.append(RetrievalConfig(top_k=10, similarity_threshold=0.6, use_mmr=use_mmr))
        return configs

    def record_trial(self, config: RetrievalConfig, metrics: dict[str, float]) -> RetrievalTrial:
        trial = RetrievalTrial(config=config, metrics=metrics)
        recall_keys = [k for k in metrics if "recall" in k.lower()]
        precision_keys = [k for k in metrics if "precision" in k.lower()]
        recall_val = sum(metrics[k] for k in recall_keys) / len(recall_keys) if recall_keys else 0
        precision_val = sum(metrics[k] for k in precision_keys) / len(precision_keys) if precision_keys else 0
        trial.score = (recall_val + precision_val) / 2
        self._trials.append(trial)
        return trial

    def best_config(self) -> Optional[RetrievalConfig]:
        if not self._trials:
            return None
        best = max(self._trials, key=lambda t: t.score)
        return best.config

    def top_n(self, n: int = 5) -> list[RetrievalTrial]:
        sorted_trials = sorted(self._trials, key=lambda t: t.score, reverse=True)
        return sorted_trials[:n]

    def summary(self) -> dict[str, Any]:
        if not self._trials:
            return {"trials": 0, "best": None}
        best = self.best_config()
        return {
            "trials": len(self._trials),
            "best": {
                "top_k": best.top_k,
                "similarity_threshold": best.similarity_threshold,
                "rerank": best.rerank,
                "hybrid_search": best.hybrid_search,
                "use_mmr": best.use_mmr,
                "score": max(t.score for t in self._trials),
            } if best else None,
            "top_5": [
                {"top_k": t.config.top_k, "threshold": t.config.similarity_threshold,
                 "rerank": t.config.rerank, "score": t.score}
                for t in self.top_n(5)
            ],
        }
