from app.query_processing.question_decomposer import QuestionDecomposer


class TestQuestionDecomposer:
    def setup_method(self):
        self.decomposer = QuestionDecomposer(max_sub_questions=5)

    def test_decompose_empty(self):
        assert self.decomposer.decompose("") == []
        assert self.decomposer.decompose("   ") == []

    def test_simple_question(self):
        result = self.decomposer.decompose("What is my blood pressure?")
        assert len(result) == 1
        assert result[0].requires_retrieval

    def test_compound_question_and(self):
        result = self.decomposer.decompose(
            "What is my blood pressure and what is my cholesterol?"
        )
        assert len(result) >= 1

    def test_multi_sentence(self):
        result = self.decomposer.decompose(
            "What medications am I taking? What is my diagnosis?"
        )
        assert len(result) >= 2

    def test_infer_intent_informational(self):
        result = self.decomposer.decompose("What is diabetes?")
        assert result[0].intent.value == "informational" or result[0].intent.value == "factual"

    def test_infer_intent_instructional(self):
        result = self.decomposer.decompose("How do I take metformin?")
        assert result[0].intent.value in ("instructional", "factual")

    def test_infer_intent_comparative(self):
        result = self.decomposer.decompose("Compare metformin and insulin")
        assert result[0].intent.value == "comparative"

    def test_infer_intent_administrative(self):
        result = self.decomposer.decompose("When is my next appointment?")
        assert result[0].intent.value == "administrative"

    def test_limits_sub_questions(self):
        tiny = QuestionDecomposer(max_sub_questions=2)
        parts = tiny.decompose("A? B? C? What is D?")
        assert len(parts) <= 2
