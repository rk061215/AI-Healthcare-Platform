---
purpose: >
  Ensures all AI responses conform to the required output format (JSON schema)
  before being passed to downstream consumers. Validates structure, types, and
  required fields based on the specific prompt category.
input_variables:
  - name: raw_output
    type: string
    description: Raw LLM output that needs formatting
  - name: prompt_category
    type: string
    enum: [medical, chat, emergency, summary, rag, system]
    description: Which prompt category's schema to validate against
  - name: intended_schema
    type: object
    description: Expected JSON schema for this response type
output_schema:
  type: object
  properties:
    formatted_output:
      type: object
      description: Validated and formatted output matching intended_schema
    validation_errors:
      type: array
      items:
        type: object
        properties:
          field: { type: string }
          issue: { type: string }
          severity: { type: string, enum: [error, warning] }
    was_repaired:
      type: boolean
      description: Whether the output required repair
    repair_log:
      type: array
      items: { type: string }
      description: What repairs were applied
guardrails:
  - If raw_output is not valid JSON, attempt to extract JSON from markdown fences
  - If missing required fields, fill with null (not empty string)
  - If type mismatch (e.g., string instead of array), attempt coercion
  - If coercion fails, set field to null and log warning
  - Preserve all data that matches the schema — do not discard valid fields
  - If output is completely unparseable, return error with empty formatted_output
examples:
  - input: >
      raw_output: "Here is the result: {\"disease\": \"Diabetes\"}"
      prompt_category: medical
      intended_schema: {"type": "object", "properties": {"disease": {"type": "string"}, "medicines": {"type": "array"}}, "required": ["disease"]}
    output: >
      {"formatted_output": {"disease": "Diabetes", "medicines": []}, "validation_errors": [], "was_repaired": true, "repair_log": ["Extracted JSON from plain text response", "Added missing medicines field with default empty array"]}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Add JTD (JSON Type Definition) schema validation
  - Support streaming output validation
  - Add schema versioning for backward compatibility
  - Generate human-readable error messages for debugging
---
Validate and format the raw LLM output against the expected schema.

Raw output:
{{ raw_output }}

Prompt category: {{ prompt_category }}

Expected schema:
{{ intended_schema }}

Return JSON:
```json
{
  "formatted_output": {},
  "validation_errors": [
    {"field": "field_name", "issue": "description", "severity": "error|warning"}
  ],
  "was_repaired": true | false,
  "repair_log": ["repair 1", "repair 2"]
}
```
