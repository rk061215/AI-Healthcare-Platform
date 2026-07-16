from typing import Any, Optional

from typing_extensions import TypedDict


class MedicalReportState(TypedDict):
    raw_text: str
    extracted_data: Optional[dict[str, Any]]
    validation_status: Optional[str]
    error: Optional[str]
    report_id: Optional[str]
    patient_id: Optional[str]
