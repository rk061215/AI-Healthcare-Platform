from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ChunkConfig:
    chunk_size: int = 512
    chunk_overlap: int = 64
    strategy: str = "recursive"


@dataclass
class ChunkTrial:
    config: ChunkConfig
    metrics: dict[str, float] = field(default_factory=dict)
    score: float = 0.0


class ChunkOptimizer:
    def __init__(self):
        self._trials: list[ChunkTrial] = []

    @property
    def trials(self) -> list[ChunkTrial]:
        return list(self._trials)

    def suggest_sizes(
        self,
        min_size: int = 128,
        max_size: int = 2048,
        step: int = 128,
        overlaps: Optional[list[int]] = None,
    ) -> list[ChunkConfig]:
        configs: list[ChunkConfig] = []
        overlaps = overlaps or [0, 32, 64, 128]
        for size in range(min_size, max_size + 1, step):
            for overlap in overlaps:
                if overlap < size:
                    configs.append(ChunkConfig(chunk_size=size, chunk_overlap=overlap))
        return configs

    def suggest_strategies(self) -> list[ChunkConfig]:
        base_sizes = [256, 512, 768, 1024]
        strategies = ["fixed", "recursive", "semantic", "sentence"]
        configs: list[ChunkConfig] = []
        for s in strategies:
            for size in base_sizes:
                configs.append(ChunkConfig(chunk_size=size, chunk_overlap=64, strategy=s))
        return configs

    def record_trial(self, config: ChunkConfig, metrics: dict[str, float]) -> ChunkTrial:
        trial = ChunkTrial(config=config, metrics=metrics)
        relevant = [v for k, v in metrics.items() if "recall" in k.lower() or "f1" in k.lower()]
        trial.score = sum(relevant) / len(relevant) if relevant else 0.0
        self._trials.append(trial)
        return trial

    def best_config(self) -> Optional[ChunkConfig]:
        if not self._trials:
            return None
        best = max(self._trials, key=lambda t: t.score)
        return best.config

    def top_n(self, n: int = 5) -> list[ChunkTrial]:
        sorted_trials = sorted(self._trials, key=lambda t: t.score, reverse=True)
        return sorted_trials[:n]

    def summary(self) -> dict[str, Any]:
        if not self._trials:
            return {"trials": 0, "best": None}
        best = self.best_config()
        return {
            "trials": len(self._trials),
            "best": {
                "chunk_size": best.chunk_size,
                "chunk_overlap": best.chunk_overlap,
                "strategy": best.strategy,
                "score": max(t.score for t in self._trials),
            } if best else None,
            "top_5": [
                {"chunk_size": t.config.chunk_size, "chunk_overlap": t.config.chunk_overlap,
                 "strategy": t.config.strategy, "score": t.score}
                for t in self.top_n(5)
            ],
        }
