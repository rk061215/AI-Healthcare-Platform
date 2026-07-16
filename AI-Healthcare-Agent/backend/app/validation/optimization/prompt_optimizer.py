from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PromptVariant:
    name: str
    template: str
    system_prompt: str = ""
    temperature: float = 0.3
    max_tokens: int = 1024
    top_p: float = 0.95


@dataclass
class PromptTrial:
    variant: PromptVariant
    metrics: dict[str, float] = field(default_factory=dict)
    score: float = 0.0


class PromptOptimizer:
    def __init__(self):
        self._trials: list[PromptTrial] = []
        self._variants: dict[str, PromptVariant] = {}

    @property
    def trials(self) -> list[PromptTrial]:
        return list(self._trials)

    @property
    def variants(self) -> dict[str, PromptVariant]:
        return dict(self._variants)

    def register_variant(self, variant: PromptVariant) -> None:
        self._variants[variant.name] = variant

    def remove_variant(self, name: str) -> bool:
        return self._variants.pop(name, None) is not None

    def get_variant(self, name: str) -> Optional[PromptVariant]:
        return self._variants.get(name)

    def record_trial(self, variant_name: str, metrics: dict[str, float]) -> Optional[PromptTrial]:
        variant = self._variants.get(variant_name)
        if variant is None:
            return None
        trial = PromptTrial(variant=variant, metrics=metrics)
        relevance = metrics.get("answer_relevance", 0)
        grounded = metrics.get("groundedness", 0)
        hallucination = 1 - metrics.get("hallucination_rate", 0)
        trial.score = (relevance * 0.4 + grounded * 0.4 + hallucination * 0.2)
        self._trials.append(trial)
        return trial

    def best_variant(self) -> Optional[PromptVariant]:
        if not self._trials:
            return None
        best = max(self._trials, key=lambda t: t.score)
        return best.variant

    def top_n(self, n: int = 3) -> list[PromptTrial]:
        sorted_trials = sorted(self._trials, key=lambda t: t.score, reverse=True)
        return sorted_trials[:n]

    def summary(self) -> dict[str, Any]:
        if not self._trials:
            return {"variants_registered": len(self._variants), "trials": 0, "best": None}
        best = self.best_variant()
        return {
            "variants_registered": len(self._variants),
            "trials": len(self._trials),
            "best": {
                "name": best.name,
                "temperature": best.temperature,
                "max_tokens": best.max_tokens,
                "score": max(t.score for t in self._trials),
            } if best else None,
            "top_n": [
                {"name": t.variant.name, "score": t.score} for t in self.top_n(5)
            ],
        }
