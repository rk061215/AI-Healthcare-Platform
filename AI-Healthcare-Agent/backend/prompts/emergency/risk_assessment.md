---
purpose: >
  Secondary risk assessment prompt that reviews the initial triage output and
  patient history to determine if escalation is needed. Acts as a safety check
  before storing an alert or notifying a doctor.
input_variables:
  - name: triage_result
    type: object
    description: The output from the symptom_triage prompt
  - name: patient_history
    type: string
    description: Summary of patient's recent interactions, adherence, and alerts
  - name: doctor_availability
    type: string
    description: Whether the assigned doctor is on duty (available, unavailable, emergency)
output_schema:
  type: object
  properties:
    escalate:
      type: boolean
      description: Whether to escalate to a doctor immediately
    escalation_reason:
      type: string | null
      description: Why escalation is or isn't needed
    suggested_action:
      type: string
      enum: [immediate_contact, schedule_appointment, monitor_and_reassess, no_action]
      description: Recommended next step
    notify_doctor:
      type: boolean
      description: Whether to push a notification to the assigned doctor
    notify_patient:
      type: string
      description: Message to send to the patient
guardrails:
  - If triage risk_level is HIGH, escalate must be true regardless of patient history
  - If triage risk_level is MEDIUM and patient has multiple recent alerts, escalate should be considered
  - If doctor is unavailable, set notify_doctor to true (queued notification) but suggest patient go to ER
  - If the patient has a history of false alarms (multiple LOW alerts without issues), reduce escalation sensitivity
  - Never override a HIGH triage assessment — always escalate
examples:
  - input: >
      triage_result: {"risk_level": "HIGH", "analysis": "Chest pain", "recommendations": ["Call 911"]}
      patient_history: "No recent alerts. Discharged 3 days ago."
      doctor_availability: "available"
    output: >
      {"escalate": true, "escalation_reason": "HIGH risk triage with chest pain in recently discharged post-surgery patient", "suggested_action": "immediate_contact", "notify_doctor": true, "notify_patient": "Please call emergency services immediately. Your doctor has been notified."}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Add escalation threshold configuration per doctor/hospital
  - Time-of-day aware escalation (night vs day different thresholds)
  - Add secondary review by another AI model for HIGH risk cases
  - Integrate with hospital on-call schedules
---
Review the triage result and patient history to determine escalation.

Triage result:
{{ triage_result }}

Patient history:
{{ patient_history }}

Doctor availability: {{ doctor_availability }}

Return JSON:
```json
{
  "escalate": true | false,
  "escalation_reason": "explanation or null",
  "suggested_action": "immediate_contact | schedule_appointment | monitor_and_reassess | no_action",
  "notify_doctor": true | false,
  "notify_patient": "message to patient"
}
```
