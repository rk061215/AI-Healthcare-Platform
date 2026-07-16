from app.ocr.structured_extractor import extract_structured_data


def test_extract_patient_name():
    text = "Patient Name: John Doe\nDate: 2024-01-15"
    result = extract_structured_data(text)
    assert result["patient_name"] == "John Doe"


def test_extract_dob():
    text = "DOB: 1985-06-20\nPatient Name: Jane Smith"
    result = extract_structured_data(text)
    assert result["patient_dob"] == "1985-06-20"


def test_extract_diagnosis():
    text = "Diagnosis: Type 2 Diabetes Mellitus"
    result = extract_structured_data(text)
    assert result["diagnosis"] == "Type 2 Diabetes Mellitus"


def test_extract_doctor_name():
    text = "Dr. Sarah Johnson\nCardiology Department"
    result = extract_structured_data(text)
    assert result["doctor_name"] == "Sarah Johnson"


def test_extract_medications():
    text = """Medications:
Lisinopril 10mg once daily
Amlodipine 5mg once daily
Atorvastatin 20mg at bedtime"""
    result = extract_structured_data(text)
    assert len(result["medications"]) == 3
    assert result["medications"][0]["name"] == "Lisinopril"
    assert result["medications"][0]["dosage"] == "10mg"
    assert result["medications"][1]["name"] == "Amlodipine"
    assert result["medications"][1]["dosage"] == "5mg"


def test_extract_lab_results():
    text = """Lab Results:
Blood Pressure: 145/95 mmHg
Heart Rate: 78 bpm
Temperature: 98.6 F"""
    result = extract_structured_data(text)
    assert len(result["lab_results"]) == 3
    assert result["lab_results"][0]["test"] == "Blood Pressure"
    assert result["lab_results"][0]["value"] == "145/95"
    assert result["lab_results"][0]["unit"] == "mmHg"


def test_extract_notes():
    text = """Notes:
Patient reports mild headache. Follow-up in 2 weeks.
Rx: Lisinopril 10mg #30"""
    result = extract_structured_data(text)
    assert result["notes"] is not None
    assert "headache" in result["notes"]


def test_empty_text():
    result = extract_structured_data("")
    assert result == {}


def test_extract_document_date():
    text = "Date of Service: 2024-03-15\nPatient: Bob"
    result = extract_structured_data(text)
    assert result["document_date"] == "2024-03-15"


def test_medication_without_section_fallback():
    text = "Metformin 500mg twice daily with meals"
    result = extract_structured_data(text)
    assert len(result["medications"]) > 0
