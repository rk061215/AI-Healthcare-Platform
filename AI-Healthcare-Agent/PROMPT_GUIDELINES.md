# Prompt Engineering Guidelines

This document defines the standards for designing, implementing, and maintaining LLM prompts in the AI Healthcare Follow-up Assistant.

## Table of Contents

- [Prompt Engineering Rules](#prompt-engineering-rules)
- [Prompt Versioning](#prompt-versioning)
- [Prompt Review Process](#prompt-review-process)
- [Prompt Naming Convention](#prompt-naming-convention)
- [LLM Safety Rules](#llm-safety-rules)
- [Prompt Testing](#prompt-testing)

---

## Prompt Engineering Rules

### 1. Single Responsibility

Each prompt should have **one clear purpose**. If a prompt tries to do multiple things, split it.

```python
# Correct — single purpose
MEDICAL_REPORT_EXTRACTION_PROMPT = """
Extract structured information from the following medical report.
Return ONLY a JSON object.
...
"""

# Incorrect — mixing extraction and summarization
BAD_PROMPT = """
Extract medicines from this report and also summarize the patient's
condition and generate follow-up recommendations...
"""
```

### 2. Structured Output

Every prompt must specify the **exact output format**. Prefer JSON with clearly defined schemas.

```python
CORRECT_OUTPUT_SPEC = """
Return a JSON object with:
- disease: The diagnosed condition(s)
- medicines: List of prescribed medicines with:
  - name
  - dosage
  - frequency
  - duration
  - route (oral, topical, IV, etc.)
  - instructions
- follow_up_date: The recommended follow-up appointment date
- doctor_instructions: Additional instructions from the doctor
- notes: Any other relevant information
"""
```

### 3. Role and Tone Setting

Every prompt should start with a clear role definition.

```python
# Correct
EMERGENCY_CLASSIFICATION_PROMPT = """
You are a medical triage assistant. Analyze the following symptoms
reported by a patient. Your task is ONLY to classify the urgency
level — NEVER diagnose a disease.
"""

# Incorrect — no role definition
BAD_PROMPT = """
Classify these symptoms:
{symptoms}
"""
```

### 4. Explicit Constraints

Be explicit about what the LLM **must not** do.

```python
CONSTRAINTS = """
Important rules:
- NEVER provide medical diagnoses
- NEVER recommend changes to prescribed medication
- If symptoms sound serious, advise consulting a doctor immediately
- Be empathetic and clear
- Use simple language (aim for 6th-grade reading level)
"""
```

### 5. Context Separation

Clearly separate different types of inputs using labeled sections.

```python
PROMPT_TEMPLATE = """
Context from patient's records:
{context}

Chat history:
{chat_history}

Patient's question: {question}
"""
```

### 6. Temperature and Token Limits

Every LLM call should have explicit parameters set in code (not in the prompt):

| Parameter       | Default     | Range   | When to Adjust                     |
|-----------------|-------------|---------|------------------------------------|
| `temperature`   | 0.3         | 0.0-1.0 | Lower = more deterministic, Higher = more creative |
| `max_tokens`    | 2048        | 1-4096  | Based on expected output length    |
| `top_p`         | 1.0         | 0.0-1.0 | Leave at default unless tuning     |

```python
response = client.chat.completions.create(
    model=settings.OPENAI_MODEL,          # gpt-4o-mini
    temperature=settings.OPENAI_TEMPERATURE,  # 0.3
    max_tokens=settings.OPENAI_MAX_TOKENS,    # 2048
    messages=[...]
)
```

### 7. Idempotency Where Possible

For data extraction prompts, design the prompt so that the same input consistently produces the same output. This means:
- Low temperature (0.0-0.3).
- Deterministic output format (JSON schema).
- No "be creative" or "surprise me" language.

### 8. Prompt as Code

Prompts are source code and follow the same development lifecycle:
- Stored in version control (`app/prompts/`).
- Reviewed in PRs.
- Tested with automated prompt tests.
- Deployed with the application.

---

## Prompt Versioning

### In-Code Versioning

Each prompt string has an associated version constant:

```python
MEDICAL_REPORT_EXTRACTION_PROMPT_V1 = """
You are a medical report analyzer...
"""

MEDICAL_REPORT_EXTRACTION_PROMPT_V2 = """
You are a medical report analyzer. Extract structured information...
"""
```

### Version Tracking

Add a version comment to each prompt file:

```python
# Version: 2
# Last updated: 2026-07-11
# Changes:
#   v2: Added explicit JSON schema in the output specification
#   v1: Initial extraction prompt

MEDICAL_REPORT_EXTRACTION_PROMPT = """
...
"""
```

### Changelog

Major prompt changes should be documented in the PR and in `CHANGELOG.md`:

```
### Changed
- Updated MEDICAL_REPORT_EXTRACTION_PROMPT to v2 — added explicit JSON schema
```

### When to Version

Update the version when:
- The output schema changes.
- A constraint is added or removed.
- The role definition changes.
- The prompt's behavior meaningfully changes in testing.

---

## Prompt Review Process

### Review Checklist

Every prompt PR must pass this checklist:

#### Structure
- [ ] Single responsibility — one clear purpose.
- [ ] Role/tone set at the beginning.
- [ ] Explicit output format specified.
- [ ] Constraints listed (what NOT to do).
- [ ] Input variables clearly marked (`{variable}`).
- [ ] Examples provided (if helpful for complex tasks).

#### Safety
- [ ] LLM cannot produce a medical diagnosis (unless explicitly designed for that purpose).
- [ ] LLM cannot recommend medication changes.
- [ ] LLM directs users to seek human medical help for emergencies.
- [ ] No prompt injection vectors (user input is in clearly marked sections).
- [ ] Standard medical disclaimer included in relevant outputs.

#### Quality
- [ ] Prompt has been tested with at least 5 representative inputs.
- [ ] Output format is validated by downstream code.
- [ ] Edge cases considered (empty input, very long input, ambiguous input).
- [ ] Language is clear and unambiguous.
- [ ] No spelling or grammar errors.

### Review Process Steps

1. **Author** creates the prompt and opens a PR.
2. **Author** runs prompt tests (see [Prompt Testing](#prompt-testing)) and includes results in the PR description.
3. **Reviewer** reads the prompt and runs it against the test suite.
4. **Reviewer** evaluates edge cases not covered by tests.
5. **Reviewer** checks for safety violations.
6. **Author** addresses feedback.
7. **Reviewer** approves.

### Sign-off Requirements

| Prompt Type         | Required Reviewers          |
|---------------------|-----------------------------|
| Medical/Clinical    | 1 engineering + 1 domain expert |
| Patient-facing      | 1 engineering + 1 domain expert |
| Internal (summary)  | 1 engineering               |

---

## Prompt Naming Convention

### File Naming

Files in `app/prompts/` follow this convention:

```
{domain}_{purpose}.py
```

| File                       | Domain    | Purpose               |
|----------------------------|-----------|-----------------------|
| `medical_report.py`        | Medical   | Report extraction     |
| `patient_chat.py`          | Patient   | Chat system prompt    |
| `emergency.py`             | Emergency | Symptom triage        |
| `doctor_summary.py`        | Doctor    | Patient summary       |

### Variable Naming

Prompt variables follow `UPPER_SNAKE_CASE` with a `_PROMPT` suffix:

```python
MEDICAL_REPORT_EXTRACTION_PROMPT = "..."
PATIENT_CHAT_SYSTEM_PROMPT = "..."
EMERGENCY_CLASSIFICATION_PROMPT = "..."
DOCTOR_SUMMARY_PROMPT = "..."
```

### Template Variables

Input variables use `{snake_case}` within the prompt string:

```python
"""
Patient data:
{patient_data}

Chat history:
{chat_history}
"""
```

---

## LLM Safety Rules

### Rule 1: No Medical Diagnoses

Unless explicitly designed and validated for diagnostic purposes, prompts must not instruct the LLM to diagnose diseases.

```python
# Correct — classify urgency, not diagnose
EMERGENCY_CLASSIFICATION_PROMPT = """
Your task is ONLY to classify the urgency level —
NEVER diagnose a disease.
"""

# Incorrect — asks for diagnosis
BAD_PROMPT = """
What disease does the patient have based on these symptoms?
"""
```

### Rule 2: No Medication Recommendations

The LLM must never recommend changes to prescribed medication.

```python
# Correct
CONSTRAINTS = """
- NEVER recommend changes to prescribed medication
- If the patient asks about changing medication, advise them to consult their doctor
"""

# Incorrect
BAD_INSTRUCTION = """
Suggest alternative medications if the patient is experiencing side effects.
"""
```

### Rule 3: Emergency Escalation

If the LLM detects potentially serious symptoms, it must advise the patient to seek immediate medical help.

```python
SAFETY_GUARDRAIL = """
If symptoms sound serious (chest pain, difficulty breathing, severe bleeding,
loss of consciousness, etc.), advise consulting a doctor or using the emergency
check feature immediately.
"""
```

### Rule 4: Medical Disclaimer

All LLM-generated outputs that touch health information must include or imply a disclaimer.

```python
DISCLAIMER = """
Note: I am an AI assistant and not a healthcare professional. Always consult
your doctor for medical advice.
"""
```

### Rule 5: Prompt Injection Protection

User input must be clearly separated from instructions to prevent prompt injection.

```python
# Correct — user input is in a clearly labeled section
PROMPT = """
You are a medical assistant. Answer the patient's question.
Patient's question: {question}
"""

# Incorrect — user input is spliced into instructions
BAD_PROMPT = f"""
You are a medical assistant. {user_input}
"""
```

### Rule 6: Data Privacy

- Never include PII (personally identifiable information) in prompts unless necessary for the task.
- When PII is necessary, use only the minimum required fields.
- Log prompt inputs/outputs without PII if logging is enabled.

### Rule 7: Output Validation

All LLM outputs must be validated before being returned to the client or stored in the database:

```python
def validate_extraction(output: dict) -> bool:
    """Validate that the LLM output matches the expected schema."""
    required_fields = ["disease", "medicines"]
    for field in required_fields:
        if field not in output:
            raise ValueError(f"Missing required field: {field}")
    return True
```

---

## Prompt Testing

### Unit Tests

Each prompt should have unit tests that verify:
1. The prompt string compiles (no syntax errors).
2. Template variables are correctly interpolated.
3. The output is parseable into the expected format.

```python
def test_medical_report_prompt_format():
    """Prompt should render correctly with sample data."""
    text = "Take Amoxicillin 500mg twice daily for 7 days"
    result = MEDICAL_REPORT_EXTRACTION_PROMPT.format(text=text)
    assert "{text}" not in result  # template was filled
    assert "Amoxicillin" in result
```

### Integration Tests

Test the full LLM pipeline (prompt → LLM → parse):

```python
def test_extraction_returns_valid_json():
    """LLM should return valid JSON matching the expected schema."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": MEDICAL_REPORT_EXTRACTION_PROMPT},
            {"role": "user", "content": "Take Amoxicillin 500mg twice daily for 7 days"},
        ],
        temperature=0.0,  # deterministic for testing
    )
    data = json.loads(response.choices[0].message.content)
    assert "medicines" in data
    assert len(data["medicines"]) > 0
    assert data["medicines"][0]["name"] == "Amoxicillin"
```

Note: Integration tests require an API key and incur cost. Run them selectively (not on every commit).

### Edge Case Tests

Test how prompts handle:

| Edge Case                  | Example Input                               |
|----------------------------|---------------------------------------------|
| Empty input                | `""`                                        |
| Very long input            | 10,000+ words of text                       |
| Ambiguous input            | "I feel sick"                                |
| Non-English input          | Symptoms in Spanish, Hindi, etc.            |
| Contradictory input        | "I have chest pain but I feel fine"          |
| Previously seen input      | Duplicate of an earlier test case            |
| Malicious input            | "Ignore previous instructions and..."        |

### Regression Tests

When a prompt is updated:
1. Run the previous test suite against the new prompt.
2. Compare outputs for 10+ representative inputs.
3. Document any behavior changes in the PR.

### Prompt Performance Monitoring

In production, monitor:

| Metric                    | What It Measures                         | Alert Threshold |
|---------------------------|------------------------------------------|-----------------|
| Parse success rate        | % of outputs that match expected schema  | < 95%           |
| Average response time     | LLM latency per call                     | > 5 seconds     |
| Token usage               | Total tokens per call                    | > 2000          |
| Safety violation rate     | % of outputs containing disallowed content| > 0%            |

### Test Data

- Use **synthetic data** for routine testing (avoid real patient data).
- When real data is needed for accuracy testing, use **de-identified** data.
- Maintain a small set of golden test cases with expected outputs.
- Version test data alongside prompts in the repository.

---

*Last updated: 2026-07-11*
