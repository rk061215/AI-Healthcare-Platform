from app.query_processing.models import (
    DecomposedQuestion,
    UnderstandingIntent,
    UnderstandingResult,
)


class TestQueryProcessingModels:
    def test_understanding_result_defaults(self):
        result = UnderstandingResult(original="test", normalized="test")
        assert result.language == "en"
        assert result.word_count == 0
        assert result.intent == UnderstandingIntent.unknown
        assert result.complexity == "simple"

    def test_understanding_result_with_entities(self):
        result = UnderstandingResult(
            original="What is my metformin dosage?",
            normalized="what is my metformin dosage?",
            entities=[{"type": "medication", "value": "metformin"}],
            sub_questions=[DecomposedQuestion(text="What is my metformin dosage?")],
        )
        assert len(result.entities) == 1
        assert len(result.sub_questions) == 1

    def test_decomposed_question_defaults(self):
        q = DecomposedQuestion(text="Test question")
        assert q.requires_retrieval
        assert q.weight == 1.0

    def test_understanding_intent_values(self):
        assert UnderstandingIntent.factual.value == "factual"
        assert UnderstandingIntent.informational.value == "informational"
        assert UnderstandingIntent.unknown.value == "unknown"
