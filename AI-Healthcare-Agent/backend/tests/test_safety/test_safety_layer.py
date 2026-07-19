from app.safety.safety_layer import SafetyLayer, SafetyConfig


class TestSafetyLayer:
    def setup_method(self):
        self.layer = SafetyLayer()

    def test_check_input_valid(self):
        result = self.layer.check_input("What is my blood pressure?")
        assert result.passed
        assert result.input_safe

    def test_check_input_empty(self):
        result = self.layer.check_input("")
        assert not result.passed

    def test_check_input_blocked_terms(self):
        config = SafetyConfig(blocked_terms=["suicide"])
        layer = SafetyLayer(config=config)
        result = layer.check_input("I want to commit suicide")
        assert not result.passed
        assert len(result.blocked_terms_found) > 0

    def test_check_output_valid(self):
        result = self.layer.check_output(
            "Your blood pressure reading is within the normal range."
        )
        assert result.passed

    def test_sanitize_output_adds_disclaimer(self):
        text = "Your test results are normal."
        sanitized = self.layer.sanitize_output(text)
        assert "educational purposes" in sanitized

    def test_sanitize_output_does_not_duplicate_disclaimer(self):
        text = "Your test results are normal.\n\nThis information is for educational purposes only. Always consult a healthcare professional for medical advice."
        sanitized = self.layer.sanitize_output(text)
        assert sanitized.count("educational purposes") == 1
