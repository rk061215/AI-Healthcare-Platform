---
purpose: >
  Verify that an extracted diagnosis is consistent with the supporting evidence
  in the report text. Flags potential extraction errors or hallucinations.
input_variables:
  - name: extracted_disease
    type: string
    description: The disease name extracted by the report analysis prompt
  - name: raw_text
    type: string
    description: The original OCR text to cross-reference
  - name: medicines
    type: array
    description: List of medicine names extracted, used as secondary evidence
output_schema:
  type: object
  properties:
    is_consistent:
      type: boolean
      description: Whether the extracted disease is supported by evidence
    confidence:
      type: string
      enum: [high, medium, low]
      description: Confidence level of the consistency check
    supporting_evidence:
      type: array
      items: { type: string }
      description: Text snippets that support the diagnosis
    contradictions:
      type: array
      items: { type: string }
      description: Text snippets that contradict or are unrelated to the diagnosis
    suggested_correction:
      type: string | null
      description: If confidence is low, suggest a more accurate diagnosis from the text
guardrails:
  - Do not apply external medical knowledge; only use text from the provided raw_text
  - If the disease is not mentioned or implied in the text, confidence must be "low"
  - Medicine names that are typical treatments for the extracted disease count as supporting evidence
  - Never suggest a diagnosis that is not present in the text
  - "If raw_text is illegible or non-medical, return is_consistent: false with confidence: low"
examples:
  - input: >
      extracted_disease: Type 2 Diabetes Mellitus
      raw_text: "Diagnosis: T2DM. Rx: Metformin 500mg bid."
      medicines: ["Metformin"]
    output: >
      {"is_consistent": true, "confidence": "high", "supporting_evidence": ["Diagnosis: T2DM"], "contradictions": [], "suggested_correction": null}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Add ICD-10 code validation
  - Integrate drug-disease indication database lookup
  - Add severity staging from text evidence
---
Verify whether the extracted disease below is consistent with the report text.

Extracted disease: {{ extracted_disease }}

Prescribed medicines: {{ medicines }}

Report text:
```
{{ raw_text }}
```

Return a JSON object:
```json
{
  "is_consistent": true | false,
  "confidence": "high" | "medium" | "low",
  "supporting_evidence": ["text snippet 1", ...],
  "contradictions": ["text snippet 1", ...],
  "suggested_correction": "more accurate disease or null"
}
```
