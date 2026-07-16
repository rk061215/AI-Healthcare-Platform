---
purpose: >
  Extract individual medicine entries from unstructured text with high precision.
  Used when the full report analysis has already identified disease context but
  the medicine list needs separate parsing (e.g. multi-page prescriptions).
input_variables:
  - name: medicine_text
    type: string
    description: Text block containing one or more medicine entries
  - name: known_disease
    type: string
    description: Pre-extracted disease context to help disambiguate medicine purpose
output_schema:
  type: object
  properties:
    medicines:
      type: array
      items:
        type: object
        properties:
          name: { type: string, description: Medicine name }
          dosage: { type: string, description: Dosage with unit }
          frequency: { type: string, description: Dosing schedule }
          duration: { type: string | null, description: Treatment course duration }
          route: { type: string, description: Administration route }
          timing: { type: string, description: Time of day (morning, evening, etc.) }
          instructions: { type: string, description: Food/activity-related instructions }
          purpose: { type: string, description: Why this medicine was prescribed }
guardrails:
  - Every medicine must have at minimum a name (even if "unknown")
  - Dosage must include numeric value + unit (mg, ml, mcg, g, IU)
  - Route must be one of: oral, topical, IV, IM, subcutaneous, inhalation, ophthalmic, otic, rectal, vaginal, other
  - If route is not specified, default to "oral"
  - Do not merge combination drugs into separate entries — keep as single entry with "/" in name
  - Flag duplicate medicines at different dosages with a note
examples:
  - input: >
      medicine_text: Amoxicillin 500mg three times a day for 7 days
      known_disease: Bacterial infection
    output: >
      {"medicines": [{"name": "Amoxicillin", "dosage": "500mg", "frequency": "three times a day", "duration": "7 days", "route": "oral", "timing": "", "instructions": "", "purpose": "Bacterial infection"}]}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Add strength normalization (e.g. "500 mg" vs "500mg")
  - Detect PRN (as needed) medications and mark them
  - Parse complex tapering schedules (e.g. "20mg x 1wk, then 10mg x 1wk")
  - Add brand/generic name cross-reference
---
Extract individual medicine entries from the medical text below.

Known disease context: {{ known_disease }}

Return a JSON object with the following structure:
```json
{
  "medicines": [
    {
      "name": "...",
      "dosage": "...",
      "frequency": "...",
      "duration": "... or null",
      "route": "oral|topical|IV|IM|subcutaneous|inhalation|ophthalmic|otic|rectal|vaginal|other",
      "timing": "... or empty string",
      "instructions": "... or empty string",
      "purpose": "... or empty string"
    }
  ]
}
```

Medicine text:
```
{{ medicine_text }}
```
