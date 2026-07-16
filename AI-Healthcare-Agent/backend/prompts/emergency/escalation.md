---
purpose: >
  Generate a structured escalation notification for the doctor when an emergency
  alert is triggered. Produces a concise clinical handoff message including
  patient summary, symptoms, triage assessment, and recommended actions.
input_variables:
  - name: patient_info
    type: object
    description: Patient name, age, condition, discharge date
  - name: symptoms
    type: string
    description: Original symptom report from patient
  - name: triage_summary
    type: object
    description: Risk level, analysis, and recommendations from triage
  - name: recent_context
    type: string
    description: Recent patient activity (medication changes, recent chats, adherence issues)
output_schema:
  type: object
  properties:
    doctor_alert:
      type: object
      properties:
        priority: { type: string, enum: [STAT, urgent, routine] }
        patient_summary: { type: string, description: One-line patient identification and condition }
        presenting_complaint: { type: string, description: The symptoms in clinical language }
        assessment: { type: string, description: AI triage assessment }
        recommended_action: { type: string, description: Suggested next step for the doctor }
        additional_context: { type: string, description: Relevant recent history }
    patient_message:
      type: object
      properties:
        instruction: { type: string, description: What the patient should do now }
        reassurance: { type: string, description: Reassuring message }
    metadata:
      type: object
      properties:
        alert_id: { type: string, description: UUID placeholder for the alert record }
        generated_at: { type: string, description: ISO timestamp }
guardrails:
  - STAT priority only for HIGH risk with active critical symptoms
  - Patient message must include actionable instruction and reassurance
  - Do not include information not present in the input variables
  - Use clinical but concise language in doctor_alert; simple language in patient_message
  - Always include the disclaimer that this is an AI-generated alert
examples:
  - input: >
      patient_info: {"name": "Alice Johnson", "age": 58, "condition": "Post-CABG surgery", "discharge_date": "2026-07-11"}
      symptoms: "Sharp chest pain, worse when breathing deeply"
      triage_summary: {"risk_level": "HIGH", "analysis": "Possible post-surgical complication"}
      recent_context: "Patient was discharged 3 days ago. No recent medication changes. Adherence to pain medication has been good."
    output: >
      {"doctor_alert": {"priority": "STAT", "patient_summary": "Alice Johnson, 58, post-CABG (discharged 2026-07-11)", "presenting_complaint": "Acute onset sharp chest pain exacerbated by deep inspiration", "assessment": "HIGH risk — possible post-surgical complication (pericarditis, pulmonary embolism)", "recommended_action": "Immediate patient contact recommended. Advise patient to proceed to ER.", "additional_context": "Discharged 3 days ago. Good medication adherence."}, "patient_message": {"instruction": "Please call emergency services (911) immediately or go to the nearest emergency room. Do not drive yourself.", "reassurance": "Your doctor has been notified and is aware of your situation. Help is on the way."}, "metadata": {"alert_id": "<will-be-assigned>", "generated_at": "<current-timestamp>"}}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Add specific ER referral recommendations based on patient location
  - Include relevant medication allergies in the alert
  - Add imaging/lab recommendations based on symptoms
  - Generate pre-filled EHR note for doctor
---
Generate an escalation notification for a doctor based on a triaged emergency alert.

Patient info:
{{ patient_info }}

Original symptoms:
{{ symptoms }}

Triage assessment:
{{ triage_summary }}

Recent patient context:
{{ recent_context }}

Return JSON:
```json
{
  "doctor_alert": {
    "priority": "STAT | urgent | routine",
    "patient_summary": "...",
    "presenting_complaint": "...",
    "assessment": "...",
    "recommended_action": "...",
    "additional_context": "..."
  },
  "patient_message": {
    "instruction": "...",
    "reassurance": "..."
  },
  "metadata": {
    "alert_id": "<will-be-assigned>",
    "generated_at": "<current-timestamp>"
  }
}
```
