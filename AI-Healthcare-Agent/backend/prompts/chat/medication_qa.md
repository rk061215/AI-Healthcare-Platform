---
purpose: >
  Focused Q&A prompt for answering specific medication-related questions. Used
  when the router detects the patient's question is exclusively about medicines
  (dosage, side effects, interactions, schedule).
input_variables:
  - name: question
    type: string
    description: The patient's medication-specific question
  - name: medicines
    type: array
    description: List of patient's active medicines with full details
  - name: allergies
    type: array
    description: Patient's known allergies (from records)
output_schema:
  type: object
  properties:
    answer:
      type: string
      description: Direct answer to the medication question
    confidence:
      type: string
      enum: [high, medium, low]
      description: How confident the answer is based on available data
    side_effects_mentioned:
      type: array
      items: { type: string }
      description: Side effects mentioned in the answer (if any)
    suggests_doctor_consult:
      type: boolean
      description: Whether the answer recommends consulting a doctor
guardrails:
  - Only answer based on the patient's specific medicines; do not infer other treatments
  - For side effect questions, list common side effects but emphasize they vary per person
  - If the medicine is not in the patient's active list, state that you cannot find it
  - Never suggest dosage changes — always recommend consulting the prescribing doctor
  - For interaction questions, check all active medicines and flag potential interactions
  - Use only the provided medicine data; do not reference external drug databases
examples:
  - input: >
      question: "Can I take ibuprofen with my Metformin?"
      medicines: [{"name": "Metformin", "dosage": "500mg", "frequency": "twice daily"}]
      allergies: []
    output: >
      {"answer": "Metformin is generally safe to take with ibuprofen, but you should check with your doctor before combining any new medication. I don't have a complete drug interaction database, so please consult your pharmacist or doctor.", "confidence": "medium", "side_effects_mentioned": [], "suggests_doctor_consult": true}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Integrate with a drug interaction API (e.g., RxNorm, OpenFDA)
  - Add food interaction warnings (e.g., grapefruit, alcohol)
  - Support dosage calculation verification
  - Add pregnancy/lactation safety checks
---
Answer the patient's medication question using their active medicine list.

Patient's active medicines:
{{ medicines }}

Known allergies:
{{ allergies }}

Question:
{{ question }}

Return JSON:
```json
{
  "answer": "your detailed answer",
  "confidence": "high|medium|low",
  "side_effects_mentioned": ["side effect 1", "side effect 2"],
  "suggests_doctor_consult": true|false
}
```
