---
purpose: >
  Generate a pre-appointment brief for the doctor summarizing the patient's
  status since the last visit. Used before follow-up appointments to give the
  doctor a quick update without reviewing all records.
input_variables:
  - name: patient_name
    type: string
    description: Patient's full name
  - name: last_appointment
    type: string
    description: Date and reason for last appointment
  - name: changes_since_last
    type: object
    description: Medication changes, new reports, new alerts since last visit
  - name: pending_actions
    type: array
    description: Any pending follow-up items from last visit
  - name: upcoming_appointment
    type: string
    description: Date and type of upcoming appointment
output_schema:
  type: object
  properties:
    brief:
      type: string
      description: 3-4 sentence summary for the doctor
    key_changes:
      type: array
      items: { type: string }
      description: What changed since last visit
    pending_items:
      type: array
      items: { type: string }
      description: Items from last visit still needing attention
    suggested_discussion_topics:
      type: array
      items: { type: string }
      description: Talking points for the appointment
guardrails:
  - Only report changes that are documented in the input data
  - Flag any new HIGH alerts as a key change
  - If adherence dropped >10% since last visit, include it as a discussion topic
  - Keep the brief under 5 sentences for quick scanning
  - Do not include outdated information from before the last appointment
examples:
  - input: >
      patient_name: "Carol Williams"
      last_appointment: "2026-06-30 — Post-discharge follow-up"
      changes_since_last: {"medication_changes": "Metformin increased from 500mg to 1000mg", "new_reports": "HbA1c recheck", "new_alerts": "One LOW alert for mild headache (resolved)"}
      pending_actions: ["Schedule lipid panel"]
      upcoming_appointment: "2026-07-20 — Routine follow-up"
    output: >
      {"brief": "Carol Williams returns for follow-up since 2026-06-30 post-discharge visit. Metformin was increased to 1000mg. HbA1c recheck results available. Lipid panel is still pending.", "key_changes": ["Metformin increased 500mg → 1000mg", "New HbA1c results available", "One resolved LOW alert for headache"], "pending_items": ["Lipid panel not yet completed"], "suggested_discussion_topics": ["Review HbA1c results and Metformin tolerability", "Discuss completing lipid panel", "Check adherence to increased Metformin dose"]}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Add expected lab values comparison (normal ranges)
  - Integrate with EHR calendar for automatic pre-appointment generation
  - Add patient-reported outcome measures (PROMs) tracking
  - Generate patient-facing pre-appointment questionnaire
---
Generate a pre-appointment brief for the doctor.

Patient: {{ patient_name }}
Last appointment: {{ last_appointment }}
Upcoming appointment: {{ upcoming_appointment }}

Changes since last visit:
{{ changes_since_last }}

Pending actions:
{{ pending_actions }}

Return JSON:
```json
{
  "brief": "3-4 sentence clinical brief",
  "key_changes": ["change 1", "change 2"],
  "pending_items": ["item 1", "item 2"],
  "suggested_discussion_topics": ["topic 1", "topic 2"]
}
```
