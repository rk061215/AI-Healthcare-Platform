---
purpose: >
  Generate a concise clinical summary of a patient's post-discharge status for
  review by the assigned doctor. Aggregates adherence, symptoms, alerts, chat
  history, and report data into a structured clinical brief.
input_variables:
  - name: patient_data
    type: object
    description: Patient demographics, condition, discharge date
  - name: medicines
    type: array
    description: Active medicines with dosage, frequency, and adherence rate
  - name: recent_symptoms
    type: array
    description: Symptoms reported in recent interactions
  - name: alerts
    type: array
    description: Recent emergency alerts and their resolution status
  - name: chat_summary
    type: string
    description: Summary of recent AI assistant interactions
  - name: reports
    type: array
    description: Recent reports and their key findings
output_schema:
  type: object
  properties:
    summary:
      type: object
      properties:
        patient_overview: { type: string, description: 1-2 sentence patient status snapshot }
        medication_adherence: { type: string, description: Adherence rate and notable patterns }
        reported_concerns: { type: string, description: Key symptoms and concerns raised }
        ai_interactions: { type: string, description: Notable AI chat interactions }
        recommendations: { type: string, description: Suggested follow-up actions }
    adherence_metrics:
      type: object
      properties:
        overall_rate: { type: number, description: Percentage 0-100 }
        missed_doses: { type: integer }
        improving: { type: boolean, description: Trend direction }
    risk_flags:
      type: array
      items: { type: string }
      description: Any risk flags the doctor should be aware of
    next_review_date:
      type: string | null
      format: YYYY-MM-DD
      description: Suggested next review date based on risk factors
guardrails:
  - Base all statements strictly on the provided data; do not infer or speculate
  - Adherence rate must be calculated as (doses taken / total scheduled) * 100
  - If adherence is below 70%, flag it as a risk
  - If the patient has had 2+ HIGH alerts in the past week, flag for priority review
  - Do not include recommendations that require data not present in the input
  - Use clinical but clear language suitable for a busy doctor
examples:
  - input: >
      patient_data: {"name": "Bob Smith", "age": 65, "condition": "Type 2 Diabetes, Hypertension", "discharge_date": "2026-07-01"}
      medicines: [{"name": "Metformin", "adherence_rate": 85}, {"name": "Lisinopril", "adherence_rate": 90}]
      recent_symptoms: ["Occasional dizziness in the morning"]
      alerts: [{"risk_level": "LOW", "resolved": true}]
      chat_summary: "Patient asked about Metformin timing and reported mild morning dizziness."
      reports: [{"title": "Blood Work", "date": "2026-07-10", "findings": "HbA1c 7.2, LDL 130"}]
    output: >
      {"summary": {"patient_overview": "Bob Smith, 65, discharged 2026-07-01 managing T2DM and HTN. Last HbA1c 7.2.", "medication_adherence": "Good adherence overall (Metformin 85%, Lisinopril 90%). No missed dose patterns detected.", "reported_concerns": "Mild morning dizziness reported. HbA1c at 7.2 — approaching target but room for improvement. LDL at 130 above target.", "ai_interactions": "Patient proactively asked about medication timing and reported symptoms appropriately.", "recommendations": "Consider evaluating morning dizziness (possible hypotension from Lisinopril). Consider lipid management given LDL 130."}, "adherence_metrics": {"overall_rate": 87.5, "missed_doses": 0, "improving": true}, "risk_flags": ["LDL above target", "Morning dizziness requires investigation"], "next_review_date": "2026-07-28"}
prompt_version: 2.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Add trend comparison with previous summary
  - Include predictive risk scoring (readmission risk)
  - Add medication interaction alerts in summary
  - Generate ICD-10 coded problem list
  - Support dictation-style voice summary output
---
Generate a concise clinical summary for the doctor.

## Patient data
{{ patient_data }}

## Medicines & adherence
{{ medicines }}

## Recent symptoms
{{ recent_symptoms }}

## Alerts
{{ alerts }}

## AI chat summary
{{ chat_summary }}

## Recent reports
{{ reports }}

Return JSON:
```json
{
  "summary": {
    "patient_overview": "1-2 sentence snapshot",
    "medication_adherence": "adherence details",
    "reported_concerns": "key symptoms and findings",
    "ai_interactions": "notable interactions",
    "recommendations": "suggested actions"
  },
  "adherence_metrics": {
    "overall_rate": 87.5,
    "missed_doses": 0,
    "improving": true
  },
  "risk_flags": ["flag 1", "flag 2"],
  "next_review_date": "YYYY-MM-DD or null"
}
```
