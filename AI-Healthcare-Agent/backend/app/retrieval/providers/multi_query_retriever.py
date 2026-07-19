from __future__ import annotations

import time
from typing import Any, Optional

from app.ai.config import AIProviderConfig
from app.ai.provider_factory import AIProviderFactory
from app.retrieval.base_retriever import BaseRetriever
from app.retrieval.config import RetrieverConfig
from app.retrieval.exceptions import RetrieverNotInitializedError, SearchExecutionError
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.models import RetrievalQuery, RetrievalResult, RetrievedDocument
from app.retrieval.providers.vector_retriever import VECTOR_RETRIEVER_PROVIDER_NAME, VectorRetriever

MULTI_QUERY_RETRIEVER_PROVIDER_NAME = "multi_query_retriever"

QUERY_VARIATION_PROMPT = """Generate {num_queries} different versions of the given medical query to improve document retrieval.

Each variation should:
- Rephrase the question using different medical terminology
- Focus on a different aspect of the query
- Use synonyms for key medical terms
- Be self-contained and searchable

Return a JSON object with:
{{
  "queries": ["variation 1", "variation 2", ...]
}}

Query: {query}"""


class MultiQueryRetriever(BaseRetriever):
    def __init__(
        self,
        config: Optional[RetrieverConfig] = None,
        base_retriever: Optional[BaseRetriever] = None,
        provider_factory: Optional[AIProviderFactory] = None,
        num_queries: int = 3,
    ) -> None:
        self._config = config or RetrieverConfig()
        self._base_retriever = base_retriever or VectorRetriever(config=config)
        self._provider_factory = provider_factory
        self._num_queries = num_queries
        self._llm = None
        self._initialized = False

    def initialize(self) -> None:
        self._base_retriever.initialize()
        if self._provider_factory:
            self._llm = self._provider_factory.create(
                AIProviderConfig(
                    provider=self._config.provider,
                    model=self._config.model or "gemini-2.0-flash",
                    temperature=0.3,
                    max_tokens=512,
                )
            )
        else:
            self._llm = AIProviderFactory.create(
                AIProviderConfig(
                    provider=self._config.provider,
                    model=self._config.model or "gemini-2.0-flash",
                    temperature=0.3,
                    max_tokens=512,
                )
            )
        self._initialized = True

    def _check_initialized(self) -> None:
        if not self._initialized:
            raise RetrieverNotInitializedError(
                "MultiQueryRetriever is not initialized. Call initialize() first."
            )

    def _generate_variations(self, query: str) -> list[str]:
        if not self._llm:
            return [query]

        prompt = QUERY_VARIATION_PROMPT.format(
            num_queries=self._num_queries,
            query=query,
        )

        try:
            result = self._llm.generate_structured_output(
                prompt=prompt,
                output_schema={
                    "type": "object",
                    "properties": {
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                        }
                    },
                    "required": ["queries"],
                },
            )
            variations = result.get("queries", [])
            clean = [q.strip() for q in variations if q and q.strip()]
            if clean:
                return [query] + clean[:self._num_queries]
        except Exception:
            pass

        return [query]

    def _rule_based_variations(self, query: str) -> list[str]:
        variations = [query]
        q = query.lower().strip()

        if q.startswith(("what", "who", "when", "where", "why", "how")):
            noun_phrase = q.split(maxsplit=1)[1] if len(q.split()) > 1 else q
            variations.append(f"information about {noun_phrase}")
            variations.append(f"details regarding {noun_phrase}")

        return variations[:self._num_queries + 1]

    def retrieve(self, query: RetrievalQuery) -> RetrievedDocument:
        self._check_initialized()
        start = time.perf_counter()

        try:
            variations = self._generate_variations(query.text)
        except Exception:
            variations = self._rule_based_variations(query.text)

        if len(variations) <= 1:
            return self._base_retriever.retrieve(query)

        all_results: list[list[RetrievalResult]] = []
        total_raw = 0

        for variant in variations:
            var_query = RetrievalQuery(
                text=variant,
                top_k=query.top_k,
                patient_id=query.patient_id,
                report_id=query.report_id,
                document_type=query.document_type,
                section=query.section,
                source=query.source,
                language=query.language,
                metadata_filter=query.metadata_filter,
                min_score=0.0,
            )
            try:
                result = self._base_retriever.retrieve(var_query)
                all_results.append(result.results)
                total_raw += result.total_results
            except Exception:
                pass

        if not all_results:
            return RetrievedDocument(
                query=query,
                results=[],
                total_results=0,
                returned_results=0,
                retrieval_time_ms=round((time.perf_counter() - start) * 1000, 2),
                provider=MULTI_QUERY_RETRIEVER_PROVIDER_NAME,
            )

        fused = reciprocal_rank_fusion(all_results, top_n=query.top_k)

        elapsed = (time.perf_counter() - start) * 1000

        return RetrievedDocument(
            query=query,
            results=fused,
            total_results=total_raw,
            returned_results=len(fused),
            retrieval_time_ms=round(elapsed, 2),
            provider=MULTI_QUERY_RETRIEVER_PROVIDER_NAME,
        )

    def retrieve_by_patient(
        self, patient_id: str, query: Optional[str] = None, top_k: int = 20
    ) -> RetrievedDocument:
        self._check_initialized()
        rq = RetrievalQuery(text=query or "", top_k=top_k, patient_id=patient_id)
        return self.retrieve(rq)

    def retrieve_by_report(
        self, report_id: str, query: Optional[str] = None, top_k: int = 50
    ) -> RetrievedDocument:
        self._check_initialized()
        rq = RetrievalQuery(text=query or "", top_k=top_k, report_id=report_id)
        return self.retrieve(rq)

    def retrieve_by_document_type(
        self, document_type: str, query: Optional[str] = None, top_k: int = 50
    ) -> RetrievedDocument:
        self._check_initialized()
        rq = RetrievalQuery(text=query or "", top_k=top_k, document_type=document_type)
        return self.retrieve(rq)

    def retrieve_with_scores(self, query: RetrievalQuery) -> RetrievedDocument:
        return self.retrieve(query)

    def health_check(self) -> dict[str, Any]:
        if not self._initialized:
            return {"status": "error", "error": "Not initialized"}
        return self._base_retriever.health_check()

    def close(self) -> None:
        self._initialized = False
        self._base_retriever.close()
