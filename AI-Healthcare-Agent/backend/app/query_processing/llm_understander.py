from __future__ import annotations

import json
import time
from typing import Optional

from app.ai.config import AIProviderConfig
from app.ai.provider_factory import AIProviderFactory
from app.query_processing.base import BaseQueryUnderstander
from app.query_processing.config import QueryUnderstandingConfig
from app.query_processing.entity_extractor import MedicalEntityExtractor
from app.query_processing.exceptions import UnderstandingError
from app.query_processing.models import (
    DecomposedQuestion,
    UnderstandingIntent,
    UnderstandingResult,
)
from app.query_processing.question_decomposer import QuestionDecomposer

UNDERSTANDING_SYSTEM_PROMPT = """You are a medical query understanding assistant.
Analyze the user's medical question and return a JSON object with:

{
  "intent": "factual|factoid|informational|instructional|comparative|diagnostic|prognostic|administrative|exploratory|troubleshooting|unknown",
  "confidence": 0.0-1.0,
  "complexity": "simple|moderate|complex",
  "requires_patient_context": true/false,
  "requires_recent_docs": true/false,
  "suggested_top_k": 5-20,
  "suggested_sections": ["list of document sections to search"],
  "entities": [
    {"type": "medication|dosage|lab_value|condition|symptom|anatomy|procedure|patient_demographic", "value": "extracted value", "normalized": "normalized form"}
  ],
  "sub_questions": [
    {"text": "sub-question text", "intent": "intent type", "weight": 0.0-1.0}
  ]
}

Only return valid JSON. No markdown, no explanations."""


class LLMQueryUnderstander(BaseQueryUnderstander):
    def __init__(
        self,
        config: Optional[QueryUnderstandingConfig] = None,
        provider_factory: Optional[AIProviderFactory] = None,
        entity_extractor: Optional[MedicalEntityExtractor] = None,
        question_decomposer: Optional[QuestionDecomposer] = None,
    ):
        super().__init__(config)
        self._provider_factory = provider_factory
        self._entity_extractor = entity_extractor or MedicalEntityExtractor(
            confidence_threshold=self._config.extractor_confidence_threshold
        )
        self._decomposer = question_decomposer or QuestionDecomposer(
            max_sub_questions=self._config.max_sub_questions
        )
        self._provider = None

    def _lazy_init(self) -> None:
        if self._provider is not None:
            return
        if self._provider_factory is not None:
            ai_config = AIProviderConfig(
                provider=self._config.provider,
                model=self._config.model,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )
            self._provider = self._provider_factory.create(ai_config)
        else:
            self._provider = AIProviderFactory.create(
                AIProviderConfig(
                    provider=self._config.provider,
                    model=self._config.model,
                    temperature=self._config.temperature,
                    max_tokens=self._config.max_tokens,
                )
            )

    def understand(self, query: str, context: Optional[str] = None) -> UnderstandingResult:
        start = time.perf_counter()

        if not query or not query.strip():
            raise UnderstandingError("Cannot understand empty query")

        rule_based = self._rule_based_understanding(query)

        if not self._config.enable_llm_understanding:
            elapsed = (time.perf_counter() - start) * 1000
            rule_based.processing_time_ms = round(elapsed, 2)
            rule_based.provider = "rule_based"
            return rule_based

        try:
            self._lazy_init()
            llm_result = self._llm_understanding(query, context)
            elapsed = (time.perf_counter() - start) * 1000
            llm_result.processing_time_ms = round(elapsed, 2)
            llm_result.provider = f"llm_{self._config.provider}"
            return llm_result
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            rule_based.processing_time_ms = round(elapsed, 2)
            rule_based.provider = "rule_based_fallback"
            return rule_based

    def extract_entities(self, query: str) -> list[dict]:
        entities = self._entity_extractor.extract(query)
        return [e.model_dump() for e in entities]

    def decompose(self, query: str) -> list[dict]:
        questions = self._decomposer.decompose(query)
        return [q.model_dump() for q in questions]

    def _rule_based_understanding(self, query: str) -> UnderstandingResult:
        cleaned = query.strip()
        normalized = cleaned.lower()

        raw_entities = self._entity_extractor.extract(cleaned)
        decomposed = self._decomposer.decompose(cleaned)

        has_medical = bool(raw_entities)
        total_entities = len(raw_entities)
        word_count = len(cleaned.split())

        if word_count <= 5:
            complexity = "simple"
        elif word_count <= 15:
            complexity = "moderate"
        else:
            complexity = "complex"

        return UnderstandingResult(
            original=cleaned,
            normalized=normalized,
            word_count=word_count,
            has_medical_terms=has_medical,
            intent=self._infer_intent_from_entities(raw_entities),
            confidence=0.5,
            entities=[e.model_dump() for e in raw_entities],
            sub_questions=decomposed,
            complexity=complexity,
            requires_patient_context=True,
            requires_recent_docs=total_entities > 0,
            suggested_top_k=15 if total_entities > 2 else 10,
            suggested_sections=self._suggest_sections(raw_entities),
        )

    def _llm_understanding(self, query: str, context: Optional[str] = None) -> UnderstandingResult:
        prompt = f"Query: {query}\n"
        if context:
            prompt += f"Context: {context}\n"
        prompt += "\nAnalyze this medical query and return the JSON analysis."

        try:
            result = self._provider.generate_structured_output(
                prompt=prompt,
                output_schema={
                    "type": "object",
                    "properties": {
                        "intent": {"type": "string"},
                        "confidence": {"type": "number"},
                        "complexity": {"type": "string"},
                        "requires_patient_context": {"type": "boolean"},
                        "requires_recent_docs": {"type": "boolean"},
                        "suggested_top_k": {"type": "integer"},
                        "suggested_sections": {"type": "array", "items": {"type": "string"}},
                        "entities": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "value": {"type": "string"},
                                    "normalized": {"type": "string"},
                                },
                            },
                        },
                        "sub_questions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "intent": {"type": "string"},
                                    "weight": {"type": "number"},
                                },
                            },
                        },
                    },
                    "required": ["intent", "confidence", "complexity"],
                },
                system_prompt=UNDERSTANDING_SYSTEM_PROMPT,
            )
        except Exception as exc:
            raise UnderstandingError(f"LLM understanding failed: {exc}") from exc

        raw_entities = self._entity_extractor.extract(query)
        decomposed = self._decomposer.decompose(query)

        intent_str = result.get("intent", "unknown")
        try:
            intent = UnderstandingIntent(intent_str)
        except ValueError:
            intent = UnderstandingIntent.unknown

        llm_entities = result.get("entities", [])
        combined_entities = list({
            e["value"].lower(): e
            for e in (llm_entities + [r.model_dump() for r in raw_entities])
        }.values())

        llm_sub_qs = result.get("sub_questions", [])
        combined_sub_qs = list({
            q.text.lower(): q
            for q in (
                [DecomposedQuestion(**sq) for sq in llm_sub_qs if isinstance(sq, dict)]
                + decomposed
            )
        }.values())

        return UnderstandingResult(
            original=query.strip(),
            normalized=query.strip().lower(),
            word_count=len(query.strip().split()),
            has_medical_terms=bool(raw_entities),
            intent=intent,
            confidence=float(result.get("confidence", 0.5)),
            entities=combined_entities,
            sub_questions=combined_sub_qs,
            complexity=result.get("complexity", "moderate"),
            requires_patient_context=bool(result.get("requires_patient_context", True)),
            requires_recent_docs=bool(result.get("requires_recent_docs", False)),
            suggested_top_k=int(result.get("suggested_top_k", 10)),
            suggested_sections=result.get("suggested_sections", []),
        )

    def _infer_intent_from_entities(self, entities: list) -> UnderstandingIntent:
        types = {e.type for e in entities}
        if "medication" in types or "dosage" in types:
            return UnderstandingIntent.factual
        if "condition" in types:
            return UnderstandingIntent.informational
        if "lab_value" in types:
            return UnderstandingIntent.factoid
        if "symptom" in types:
            return UnderstandingIntent.diagnostic
        return UnderstandingIntent.factual

    def _suggest_sections(self, entities: list) -> list[str]:
        sections = set()
        for e in entities:
            if e.type == "medication":
                sections.add("medication")
                sections.add("prescription")
            elif e.type == "lab_value":
                sections.add("lab_results")
                sections.add("results")
            elif e.type == "condition":
                sections.add("diagnosis")
                sections.add("assessment")
            elif e.type == "symptom":
                sections.add("symptoms")
                sections.add("assessment")
            elif e.type == "anatomy":
                sections.add("physical_examination")
                sections.add("findings")

        if not sections:
            sections.add("doctor_notes")
            sections.add("summary")

        return sorted(sections)[:5]
