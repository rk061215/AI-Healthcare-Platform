import re
from typing import Optional

from app.ocr.schemas import ExtractedField, StructuredDocument


def extract_structured_data(ocr_text: str) -> dict:
    if not ocr_text.strip():
        return {}

    doc = StructuredDocument()

    lines = ocr_text.split("\n")
    text_lower = ocr_text.lower()

    doc.patient_name = _extract_field(lines, r"(?:Patient\s*Name\s*[:.]?\s*)([A-Za-z\s]+)", "patient_name")
    doc.patient_dob = _extract_field(lines, r"(?:DOB|Date\s*of\s*Birth|Birth\s*Date)\s*[:.]?\s*([\d/\-\.]+)", "patient_dob")
    doc.document_date = _extract_field(lines, r"(?:Date|Date of Service)\s*[:.]?\s*([\d/\-\.]+)", "document_date")
    doc.doctor_name = _extract_field(lines, r"(?:Dr\.|Doctor|Physician)\s*[:.]?\s*([A-Za-z\s]+)", "doctor_name")
    doc.diagnosis = _extract_field(lines, r"(?:Diagnosis|Dx|Impression)\s*[:.]?\s*(.+)", "diagnosis")

    doc.medications = _extract_medications(lines, text_lower, ocr_text)
    doc.lab_results = _extract_lab_results(lines, text_lower)

    notes_lines: list[str] = []
    in_notes = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^(?:Notes|Comments|Remarks)\s*[:.]?\s*$", stripped, re.IGNORECASE):
            in_notes = True
            continue
        if in_notes:
            if re.match(r"^(?:--+|__+|Follow-up|Rx:)", stripped, re.IGNORECASE):
                break
            notes_lines.append(stripped)
    if notes_lines:
        doc.notes = " ".join(notes_lines)

    return doc.model_dump(exclude_none=True)


def _extract_field(lines: list[str], pattern: str, field_name: str) -> Optional[str]:
    for line in lines:
        m = re.search(pattern, line, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if val:
                return val
    return None


def _extract_medications(lines: list[str], text_lower: str, original_text: str) -> list[dict]:
    meds: list[dict] = []
    in_meds = False

    med_sections = [
        r"^(?:Medications?|Meds|Rx|Prescriptions?)\s*[:.]?\s*$",
    ]

    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(med_sections[0], stripped, re.IGNORECASE):
            in_meds = True
            continue

        if in_meds:
            if re.match(r"^(?:Lab|Diagnosis|Notes|Follow-up|--+|__+)", stripped, re.IGNORECASE):
                in_meds = False
                continue

            med_match = re.match(
                r"([A-Za-z\s]+)\s+(\d+\.?\d*\s*(?:mg|mcg|g|ml|IU|units?))\s*(.*)",
                stripped,
                re.IGNORECASE,
            )
            if med_match:
                med_name = med_match.group(1).strip()
                dosage = med_match.group(2).strip()
                instructions = med_match.group(3).strip() if med_match.group(3) else ""
                meds.append({
                    "name": med_name,
                    "dosage": dosage,
                    "instructions": instructions or None,
                })

    if not meds:
        rx_match = re.findall(
            r"([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)\s+(\d+\.?\d*\s*(?:mg|mcg|g|ml|IU))",
            original_text,
            re.IGNORECASE,
        )
        for name, dosage in rx_match:
            meds.append({"name": name.strip(), "dosage": dosage.strip()})

    return meds


def _extract_lab_results(lines: list[str], text_lower: str) -> list[dict]:
    results: list[dict] = []
    in_labs = False

    for line in lines:
        stripped = line.strip()
        if re.match(r"^(?:Lab\s*Results?|Laboratory)\s*[:.]?\s*$", stripped, re.IGNORECASE):
            in_labs = True
            continue

        if in_labs:
            if re.match(r"^(?:Medications?|Diagnosis|Notes|Follow-up|--+|__+)", stripped, re.IGNORECASE):
                in_labs = False
                continue

            lab_match = re.match(
                r"([A-Za-z\s/]+)\s*[:]?\s*([\d\.\/]+)\s*([A-Za-z/%]+)",
                stripped,
            )
            if lab_match:
                results.append({
                    "test": lab_match.group(1).strip(),
                    "value": lab_match.group(2).strip(),
                    "unit": lab_match.group(3).strip(),
                })

    return results
