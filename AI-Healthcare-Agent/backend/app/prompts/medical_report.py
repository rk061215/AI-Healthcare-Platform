MEDICAL_REPORT_EXTRACTION_PROMPT = """
You are a medical report analyzer. Extract structured information from the following prescription or medical report text.

Extract the following fields:
- disease: The diagnosed condition(s)
- medicines: List of prescribed medicines with:
  - name
  - dosage
  - frequency
  - duration
  - route (oral, topical, IV, etc.)
  - instructions
- follow_up_date: The recommended follow-up appointment date
- doctor_instructions: Additional instructions from the doctor
- notes: Any other relevant information

Return the data as a valid JSON object.

Report text:
{text}
"""
