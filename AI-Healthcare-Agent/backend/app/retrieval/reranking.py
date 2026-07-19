from __future__ import annotations

import time
from typing import Any, Optional

from app.ai.config import AIProviderConfig
from app.ai.provider_factory import AIProviderFactory
from app.retrieval.models import RetrievalResult


class Reranker:
    def __init__(
        self,
        provider_factory: Optional[AIProviderFactory] = None,
        provider: str = "gemini",
        model: str = "gemini-2.0-flash",
        temperature: float = 0.0,
        batch_size: int = 10,
    ):
        self._provider_factory = provider_factory
        self._provider_name = provider
        self._model = model
        self._temperature = temperature
        self._batch_size = batch_size
        self._llm = None

    def _lazy_init(self) -> None:
        if self._llm is not None:
            return
        config = AIProviderConfig(
            provider=self._provider_name,
            model=self._model,
            temperature=self._temperature,
            max_tokens=64,
        )
        if self._provider_factory:
            self._llm = self._provider_factory.create(config)
        else:
            self._llm = AIProviderFactory.create(config)

    def rerank(
        self, query: str, results: list[RetrievalResult], top_k: Optional[int] = None
    ) -> list[RetrievalResult]:
        if not results:
            return results

        start = time.perf_counter()

        try:
            reranked = self._llm_rerank(query, results)
        except Exception:
            reranked = self._score_rerank(query, results)

        if top_k is not None:
            reranked = reranked[:top_k]

        elapsed = (time.perf_counter() - start) * 1000
        for r in reranked:
            r.metadata["rerank_time_ms"] = round(elapsed, 2)

        return reranked

    def _llm_rerank(
        self, query: str, results: list[RetrievalResult]
    ) -> list[RetrievalResult]:
        self._lazy_init()

        scored: list[tuple[float, RetrievalResult]] = []

        for i in range(0, len(results), self._batch_size):
            batch = results[i : i + self._batch_size]
            batch_scores = self._score_batch(query, batch)
            scored.extend(zip(batch_scores, batch))

        scored.sort(key=lambda x: x[0], reverse=True)

        for score, result in scored:
            result.score = round(score, 6)
            result.metadata["rerank_score"] = result.score

        return [r for _, r in scored]

    def _score_batch(
        self, query: str, batch: list[RetrievalResult]
    ) -> list[float]:
        if len(batch) == 0:
            return []

        prompt_lines = []
        for i, doc in enumerate(batch):
            text_preview = doc.text[:500].replace("\n", " ")
            prompt_lines.append(f"[{i}] {text_preview}")

        prompt = (
            f"Query: {query}\n\n"
            f"Documents:\n" + "\n".join(prompt_lines) + "\n\n"
            f"Rate each document's relevance to the query from 0.0 (irrelevant) to 1.0 (highly relevant). "
            f"Return a JSON object with scores as an array of floats in the same order.\n"
            f'{{"scores": [0.0, 0.5, ...]}}'
        )

        try:
            result = self._llm.generate_structured_output(
                prompt=prompt,
                output_schema={
                    "type": "object",
                    "properties": {
                        "scores": {
                            "type": "array",
                            "items": {"type": "number"},
                        }
                    },
                    "required": ["scores"],
                },
            )
            scores = result.get("scores", [])
            return [float(s) for s in scores[: len(batch)]]
        except Exception:
            return [0.5] * len(batch)

    def _score_rerank(
        self, query: str, results: list[RetrievalResult]
    ) -> list[RetrievalResult]:
        query_terms = set(query.lower().split())
        for doc in results:
            doc_terms = set(doc.text.lower().split())
            overlap = len(query_terms & doc_terms)
            doc.score = overlap / max(len(query_terms), 1)
            doc.metadata["rerank_score"] = doc.score

        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def rerank_with_scores(
        self, query: str, results: list[RetrievalResult], top_k: Optional[int] = None
    ) -> tuple[list[RetrievalResult], list[float]]:
        reranked = self.rerank(query, results, top_k)
        scores = [r.score for r in reranked]
        return reranked, scores
