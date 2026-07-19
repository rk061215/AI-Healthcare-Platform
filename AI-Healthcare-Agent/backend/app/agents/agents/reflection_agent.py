from __future__ import annotations

import json
import time
from typing import Any, Optional

from app.agents.agent_context import AgentContext
from app.agents.agent_response import AgentResponse
from app.agents.agent_state import ExecutionStatus
from app.agents.base_agent import BaseAgent
from app.agents.config import AgentConfig
from app.ai.config import AIProviderConfig
from app.ai.provider_factory import AIProviderFactory
from app.rag.confidence_engine import ConfidenceEngine
from app.rag.models import CitationBlock

REFLECTION_SYSTEM_PROMPT = """You are a medical answer reviewer. Review the generated answer and provide feedback.

Check for:
1. Are all claims supported by citations?
2. Are there any contradictions?
3. Is the answer complete and accurate?
4. Are there any missing important details?
5. Is the language clear and appropriate?

Return a JSON review:
{
  "score": 0.0-1.0,
  "issues": [
    {"severity": "high|medium|low", "description": "issue description"}
  ],
  "suggestions": ["suggestion 1", "suggestion 2"],
  "revised_answer": "revised version or null if no changes needed",
  "explanation": "brief review summary"
}"""


class ReflectionAgent(BaseAgent):
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        provider_factory: Optional[AIProviderFactory] = None,
        confidence_engine: Optional[ConfidenceEngine] = None,
    ):
        super().__init__(config)
        self._provider_factory = provider_factory
        self._confidence_engine = confidence_engine or ConfidenceEngine()
        self._llm = None

    def initialize(self) -> None:
        if self._llm is None:
            ai_config = AIProviderConfig(
                provider=self._config.ai_provider or "gemini",
                model=self._config.ai_model or "gemini-2.0-flash",
                temperature=0.1,
                max_tokens=1024,
            )
            if self._provider_factory:
                self._llm = self._provider_factory.create(ai_config)
            else:
                self._llm = AIProviderFactory.create(ai_config)

    def can_handle(self, context: AgentContext) -> bool:
        return True

    def prepare_context(self, context: AgentContext) -> AgentContext:
        return context

    def retrieve_memory(self, context: AgentContext) -> AgentContext:
        return context

    def retrieve_documents(self, context: AgentContext) -> AgentContext:
        return context

    def invoke_rag(self, context: AgentContext) -> AgentResponse:
        start = time.perf_counter()

        try:
            self.initialize()

            answer = context.metadata.get("answer", "")
            citations_data = context.metadata.get("citations", [])
            citations = CitationBlock(citations=citations_data)

            confidence = self._confidence_engine.evaluate(answer, citations)

            review = self._review_answer(answer, context.query)

            elapsed = (time.perf_counter() - start) * 1000

            revised = review.get("revised_answer") or answer
            issues = review.get("issues", [])
            suggestions = review.get("suggestions", [])

            high_severity = [i for i in issues if i.get("severity") == "high"]

            return AgentResponse.ok(
                answer=revised,
                data={
                    "original_answer": answer,
                    "review": review,
                    "confidence": confidence.model_dump(),
                    "refinements_applied": revised != answer,
                },
                session_id=context.session_id,
                total_duration_ms=round(elapsed, 2),
                metadata={
                    "reflection_score": review.get("score", 0.5),
                    "issues_count": len(issues),
                    "high_severity_issues": len(high_severity),
                },
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            return AgentResponse(
                success=False,
                answer=context.metadata.get("answer", ""),
                error=str(exc),
                session_id=context.session_id,
                total_duration_ms=round(elapsed, 2),
            )

    def post_process(self, response: AgentResponse, context: AgentContext) -> AgentResponse:
        return response

    def validate_response(self, response: AgentResponse) -> AgentResponse:
        return response

    def cleanup(self) -> None:
        self._llm = None

    def reflect(
        self, answer: str, query: str, citations: Optional[CitationBlock] = None
    ) -> AgentResponse:
        context = AgentContext(
            query=query,
            session_id="reflect",
            metadata={
                "answer": answer,
                "citations": [c.model_dump() for c in citations.citations] if citations else [],
            },
        )
        return self.invoke_rag(context)

    def _review_answer(self, answer: str, query: str) -> dict[str, Any]:
        if not answer:
            return {
                "score": 0.0,
                "issues": [{"severity": "high", "description": "Empty answer"}],
                "suggestions": ["Generate a proper response"],
                "revised_answer": None,
                "explanation": "No content to review",
            }

        prompt = f"Original query: {query}\n\nGenerated answer:\n{answer}\n\nReview this answer."

        try:
            result = self._llm.generate_structured_output(
                prompt=prompt,
                output_schema={
                    "type": "object",
                    "properties": {
                        "score": {"type": "number"},
                        "issues": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "description": {"type": "string"},
                                },
                            },
                        },
                        "suggestions": {"type": "array", "items": {"type": "string"}},
                        "revised_answer": {"type": "string"},
                        "explanation": {"type": "string"},
                    },
                    "required": ["score", "issues", "explanation"],
                },
                system_prompt=REFLECTION_SYSTEM_PROMPT,
            )
            return result
        except Exception:
            return {
                "score": 0.5,
                "issues": [],
                "suggestions": ["Manual review recommended"],
                "revised_answer": None,
                "explanation": "Automated review unavailable",
            }
