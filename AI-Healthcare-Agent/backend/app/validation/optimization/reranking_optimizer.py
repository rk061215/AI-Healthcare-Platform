from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RerankingConfig:
    strategy: str = "score"
    k_to_rerank: int = 20
    final_k: int = 5
    diversity_penalty: float = 0.0
    recency_bias: float = 0.0
    section_boost: dict[str, float] = field(default_factory=dict)


@dataclass
class RerankingTrial:
    config: RerankingConfig
    metrics: dict[str, float] = field(default_factory=dict)
    score: float = 0.0


class RerankingOptimizer:
    STRATEGIES = ["score", "diversity", "hybrid", "section_boosted", "recency"]

    def __init__(self):
        self._trials: list[RerankingTrial] = []

    @property
    def trials(self) -> list[RerankingTrial]:
        return list(self._trials)

    def suggest_configs(self) -> list[RerankingConfig]:
        configs: list[RerankingConfig] = []
        for strategy in self.STRATEGIES:
            for final_k in [3, 5, 10]:
                if strategy == "diversity":
                    for penalty in [0.1, 0.3, 0.5]:
                        configs.append(RerankingConfig(
                            strategy=strategy, final_k=final_k, diversity_penalty=penalty,
                        ))
                elif strategy == "section_boosted":
                    configs.append(RerankingConfig(
                        strategy=strategy, final_k=final_k,
                        section_boost={"diagnosis": 1.5, "medication": 1.3, "treatment": 1.2},
                    ))
                elif strategy == "recency":
                    configs.append(RerankingConfig(
                        strategy=strategy, final_k=final_k, recency_bias=0.2,
                    ))
                else:
                    configs.append(RerankingConfig(strategy=strategy, final_k=final_k))
        return configs

    def record_trial(self, config: RerankingConfig, metrics: dict[str, float]) -> RerankingTrial:
        trial = RerankingTrial(config=config, metrics=metrics)
        ndcg = metrics.get("ndcg", 0)
        mrr = metrics.get("mrr", 0)
        trial.score = (ndcg + mrr) / 2
        self._trials.append(trial)
        return trial

    def best_config(self) -> Optional[RerankingConfig]:
        if not self._trials:
            return None
        best = max(self._trials, key=lambda t: t.score)
        return best.config

    def top_n(self, n: int = 5) -> list[RerankingTrial]:
        return sorted(self._trials, key=lambda t: t.score, reverse=True)[:n]

    def summary(self) -> dict[str, Any]:
        if not self._trials:
            return {"trials": 0, "best": None}
        best = self.best_config()
        return {
            "trials": len(self._trials),
            "best": {
                "strategy": best.strategy,
                "final_k": best.final_k,
                "diversity_penalty": best.diversity_penalty,
                "score": max(t.score for t in self._trials),
            } if best else None,
            "top_n": [
                {"strategy": t.config.strategy, "final_k": t.config.final_k, "score": t.score}
                for t in self.top_n(5)
            ],
        }
