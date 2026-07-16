from typing import Optional

from pydantic import BaseModel


class MedicineAdherenceSummary(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    adherence_rate: float
    total_doses: int
    missed_doses: int


class PatientSummaryResponse(BaseModel):
    patient_id: str
    patient_name: str
    period: str
    overall_adherence_rate: float
    medicines: list[MedicineAdherenceSummary]
    recent_symptoms: list[str]
    alert_count: int
    highest_risk_alert: Optional[str] = None
    chat_summary: Optional[str] = None
    doctor_notes: Optional[str] = None
    generated_at: str
