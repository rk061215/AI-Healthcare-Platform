---
purpose: >
  Safety guardrails prompt evaluated before every LLM response. Filters out
  harmful, misleading, or out-of-scope outputs before they reach the user.
  Acts as a content safety layer.
input_variables:
  - name: input_text
    type: string
    description: The patient's input message
  - name: generated_response
    type: string
    description: The raw LLM-generated response
  - name: context
    type: string
    description: Current conversation and patient context
output_schema:
  type: object
  properties:
    is_safe:
      type: boolean
      description: Whether the response passes all guardrails
    violations:
      type: array
      items:
        type: object
        properties:
          rule: { type: string, description: Which guardrail was violated }
          severity: { type: string, enum: [block, warn, flag] }
          details: { type: string, description: What triggered the violation }
    action:
      type: string
      enum: [allow, block, rewrite, escalate_human]
      description: Recommended action
    rewritten_response:
      type: string | null
      description: Safe version of the response if action is "rewrite"
guardrails:
  - BLOCK: Medical diagnosis statements (e.g., "You have diabetes")
  - BLOCK: Medication dosage changes (e.g., "Take an extra pill")
  - BLOCK: Emergency discouragement (e.g., "You don't need to go to the ER")
  - BLOCK: Protected health information of other patients
  - WARN: Speculative prognosis or outcome predictions
  - WARN: Overly confident language about treatment efficacy
  - FLAG: Frustrated or angry tone toward the patient
  - FLAG: Medical jargon without explanation
  - If a BLOCK violation is found, the response must be blocked entirely
  - If only WARN/FLAG violations are found, the response may proceed with warnings
examples:
  - input: >
      input_text: "I think I have an infection"
      generated_response: "Based on your symptoms, you have a bacterial infection and need antibiotics."
      context: "Patient has fever and wound redness"
    output: >
      {"is_safe": false, "violations": [{"rule": "No medical diagnoses", "severity": "block", "details": "Response diagnosed bacterial infection"}], "action": "block", "rewritten_response": "I understand your concern. The symptoms you described (fever and wound redness) could have several causes. Please consult your doctor for a proper diagnosis and treatment plan."}
prompt_version: 2.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Add context-aware guardrails that adapt to conversation history
  - Implement guardrail override for doctor-facing responses
  - Add legal compliance guardrails (HIPAA, GDPR keywords)
  - Support custom guardrail rules per hospital/deployment
---
Evaluate the generated response against safety guardrails.

Patient input:
{{ input_text }}

Generated response:
{{ generated_response }}

Context:
{{ context }}

Return JSON:
```json
{
  "is_safe": true | false,
  "violations": [
    {
      "rule": "name of violated rule",
      "severity": "block | warn | flag",
      "details": "what triggered the violation"
    }
  ],
  "action": "allow | block | rewrite | escalate_human",
  "rewritten_response": "safe version or null"
}
```
