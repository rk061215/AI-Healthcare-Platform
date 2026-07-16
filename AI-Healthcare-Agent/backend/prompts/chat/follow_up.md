---
purpose: >
  Generate follow-up questions after a patient interaction to encourage ongoing
  engagement, check symptom progression, and identify unreported concerns.
input_variables:
  - name: last_exchange
    type: string
    description: The last Q&A turn between patient and assistant
  - name: patient_condition
    type: string
    description: Patient's primary diagnosis or condition
  - name: days_since_discharge
    type: integer
    description: Number of days since hospital discharge
  - name: unanswered_medicines
    type: array
    description: Medicines the patient hasn't asked about yet
output_schema:
  type: object
  properties:
    follow_up_questions:
      type: array
      max_items: 3
      items:
        type: object
        properties:
          question: { type: string, description: Follow-up question text }
          category: { type: string, enum: [symptom, adherence, appointment, general] }
          priority: { type: integer, minimum: 1, maximum: 3, description: Priority (1=most important) }
guardrails:
  - Max 3 follow-up questions to avoid overwhelming the patient
  - At most 1 question should be about symptoms (to avoid anxiety)
  - Prioritize adherence questions if the patient has missed doses
  - Do not ask questions already answered in the last exchange
  - Questions must be answerable with yes/no or brief text
  - Do not generate follow-ups if risk_level is HIGH (escalate instead)
examples:
  - input: >
      last_exchange: "Patient asked about Metformin timing. Assistant answered 'take with meals'."
      patient_condition: "Type 2 Diabetes"
      days_since_discharge: 5
      unanswered_medicines: ["Lisinopril", "Atorvastatin"]
    output: >
      {"follow_up_questions": [{"question": "Have you been taking your Metformin with meals as recommended?", "category": "adherence", "priority": 1}, {"question": "Do you have any questions about your other medicines (Lisinopril or Atorvastatin)?", "category": "general", "priority": 2}, {"question": "How are you feeling overall this week?", "category": "symptom", "priority": 3}]}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Time-aware follow-up scheduling (morning vs evening questions)
  - Personalized question bank based on patient demographics
  - A/B testing different question phrasings for engagement
  - Integrate with adherence data to target missed doses
---
Generate follow-up questions for a patient after a chat interaction.

Last exchange:
{{ last_exchange }}

Patient condition: {{ patient_condition }}
Days since discharge: {{ days_since_discharge }}
Unanswered medicines: {{ unanswered_medicines }}

Return a JSON object with up to 3 follow-up questions:
```json
{
  "follow_up_questions": [
    {
      "question": "question text",
      "category": "symptom|adherence|appointment|general",
      "priority": 1
    }
  ]
}
```
