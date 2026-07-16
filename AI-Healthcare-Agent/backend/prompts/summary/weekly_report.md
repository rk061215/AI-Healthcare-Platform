---
purpose: >
  Generate a weekly patient status report for the care team. Aggregates the
  entire week's data into a summary suitable for care coordination meetings
  or documentation.
input_variables:
  - name: patient_name
    type: string
    description: Patient name
  - name: week_start
    type: string
    format: YYYY-MM-DD
    description: Start of the reporting week
  - name: week_end
    type: string
    format: YYYY-MM-DD
    description: End of the reporting week
  - name: daily_summaries
    type: array
    description: Array of per-day summaries with adherence, symptoms, interactions
  - name: alerts_this_week
    type: array
    description: All alerts generated during the week
  - name: medicine_changes
    type: array
    description: Any medication changes made this week
  - name: appointment_attendance
    type: object
    description: Scheduled vs attended appointments
output_schema:
  type: object
  properties:
    weekly_summary:
      type: string
      description: 2-3 paragraph narrative summary
    metrics:
      type: object
      properties:
        avg_adherence: { type: number, description: Average adherence for the week }
        adherence_trend: { type: string, enum: [improving, declining, stable] }
        total_alerts: { type: integer }
        high_risk_alerts: { type: integer }
        interactions_count: { type: integer }
        appointments_kept: { type: integer }
        appointments_missed: { type: integer }
    highlights:
      type: array
      items: { type: string }
      description: Positive events or improvements
    concerns:
      type: array
      items: { type: string }
      description: Areas needing attention
    recommendations:
      type: array
      items: { type: string }
      description: Suggested actions for the coming week
guardrails:
  - Base all metrics strictly on provided data; do not extrapolate
  - If no data is available for a metric, omit it rather than reporting zero
  - Highlights should celebrate genuine improvements (e.g., adherence increase, no alerts)
  - Concerns must be actionable; include suggested interventions
  - Do not include protected health information beyond what is necessary
  - Generate only on the specified week range
examples:
  - input: >
      patient_name: "Alice Johnson"
      week_start: "2026-07-07"
      week_end: "2026-07-13"
      daily_summaries: [{"date": "2026-07-07", "adherence": 100, "symptoms": [], "interactions": 0}, {"date": "2026-07-10", "adherence": 100, "symptoms": ["mild headache"], "interactions": 1}]
      alerts_this_week: [{"risk_level": "LOW", "status": "resolved"}]
      medicine_changes: []
      appointment_attendance: {"scheduled": 1, "attended": 1}
    output: >
      {"weekly_summary": "Alice had a stable week post-discharge. She maintained 100% medication adherence and attended her scheduled follow-up appointment. One LOW alert was generated for a mild headache which resolved without intervention.", "metrics": {"avg_adherence": 100, "adherence_trend": "stable", "total_alerts": 1, "high_risk_alerts": 0, "interactions_count": 1, "appointments_kept": 1, "appointments_missed": 0}, "highlights": ["Perfect medication adherence (100%)", "Attended all scheduled appointments", "No HIGH or MEDIUM alerts"], "concerns": ["One mild headache reported — monitor if recurrent"], "recommendations": ["Continue current medication regimen", "Monitor headache pattern", "Schedule next follow-up in 2 weeks"]}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Generate printable PDF report for care coordination meetings
  - Add comparison with previous week for trend visualization
  - Include predictive flags for patients at risk of deterioration
  - Support multi-patient aggregate report for care managers
---
Generate a weekly patient status report for the care team.

Patient: {{ patient_name }}
Week: {{ week_start }} to {{ week_end }}

Daily summaries:
{{ daily_summaries }}

Alerts this week:
{{ alerts_this_week }}

Medication changes:
{{ medicine_changes }}

Appointments:
{{ appointment_attendance }}

Return JSON:
```json
{
  "weekly_summary": "2-3 paragraph narrative",
  "metrics": {
    "avg_adherence": 0-100,
    "adherence_trend": "improving|declining|stable",
    "total_alerts": 0,
    "high_risk_alerts": 0,
    "interactions_count": 0,
    "appointments_kept": 0,
    "appointments_missed": 0
  },
  "highlights": ["achievement 1", "achievement 2"],
  "concerns": ["concern 1", "concern 2"],
  "recommendations": ["action 1", "action 2"]
}
```
