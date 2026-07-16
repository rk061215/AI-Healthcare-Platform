MEDICAL_EXTRACTION_PROMPT = """
You are a medical data extraction specialist. Given a prescription or medical report text,
extract all structured medical information.

Return a JSON object with:
{{
  "disease": "diagnosed condition",
  "medicines": [
    {{
      "name": "medicine name",
      "dosage": "dosage amount",
      "frequency": "how often to take",
      "duration": "treatment duration",
      "route": "administration route",
      "instructions": "special instructions"
    }}
  ],
  "follow_up_date": "YYYY-MM-DD or null",
  "doctor_instructions": "summary of doctor's instructions",
  "notes": "additional notes"
}}

Text: {text}
"""
