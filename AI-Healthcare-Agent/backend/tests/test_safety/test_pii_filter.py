from app.safety.pii_filter import PIIFilter


class TestPIIFilter:
    def setup_method(self):
        self.filter_ = PIIFilter(enabled=True)

    def test_filter_ssn(self):
        result = self.filter_.filter("My SSN is 123-45-6789")
        assert "[REDACTED]" in result
        assert "123-45-6789" not in result

    def test_filter_phone(self):
        result = self.filter_.filter("Call me at 555-123-4567")
        assert "[REDACTED]" in result

    def test_filter_email(self):
        result = self.filter_.filter("Email me at test@example.com")
        assert "[REDACTED]" in result

    def test_detect_pii(self):
        detections = self.filter_.detect("SSN: 123-45-6789, Phone: 555-123-4567")
        types = [d["type"] for d in detections]
        assert "ssn" in types
        assert "phone" in types

    def test_contains_pii(self):
        assert self.filter_.contains_pii("My SSN is 123-45-6789")
        assert not self.filter_.contains_pii("What is my blood pressure?")

    def test_disabled_filter(self):
        disabled = PIIFilter(enabled=False)
        result = disabled.filter("SSN: 123-45-6789")
        assert "[REDACTED]" not in result
