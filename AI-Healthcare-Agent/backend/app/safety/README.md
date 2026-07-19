# Safety Layer

Input/output validation, PII detection, and medical safety checks. Part of Phase V.

## Components

### SafetyLayer
- Input safety — length limits, blocked terms
- Output safety — PII detection, medical safety warnings
- Sanitization — PII redaction, disclaimer appending

### PIIFilter
Detects and redacts: SSN, phone numbers, email addresses, credit cards, passport numbers, Medicare IDs.

## Usage
```python
from app.safety import SafetyLayer

layer = SafetyLayer()
result = layer.check_input("What is my blood pressure?")
assert result.passed

safe_output = layer.sanitize_output("Your BP is 120/80.")
# Appends medical disclaimer
```
