---
purpose: >
  Format citations for LLM responses that reference retrieved documents.
  Ensures consistent, verifiable citation formatting across all AI responses.
input_variables:
  - name: response_text
    type: string
    description: The LLM-generated response before citations
  - name: source_documents
    type: array
    description: Documents used to generate the response
output_schema:
  type: object
  properties:
    cited_response:
      type: string
      description: Response text with inline citations
    citations:
      type: array
      items:
        type: object
        properties:
          id: { type: integer, description: Citation number }
          document: { type: string, description: Document title or type }
          date: { type: string, description: Document date }
          excerpt: { type: string, description: Snippet of relevant text }
    uncited_statements:
      type: array
      items: { type: string }
      description: Statements in the response that could not be attributed to sources
guardrails:
  - Every factual claim in the response must have at least one citation
  - "Citations use numerical superscript format: [1], [2], etc."
  - If a statement cannot be attributed to any source, flag it as uncited
  - General advice ("consult your doctor") does not need a citation
  - If the same source is cited multiple times, reuse the same citation number
  - Include the specific excerpt that supports each claim
examples:
  - input: >
      response_text: "Your Lisinopril dosage is 10mg taken once daily. This helps manage your blood pressure."
      source_documents: [{"title": "Discharge Prescription", "date": "2026-07-01", "text": "Lisinopril 10mg once daily"}, {"title": "Patient Education", "date": "2026-06-15", "text": "Lisinopril is an ACE inhibitor used to treat hypertension"}]
    output: >
      {"cited_response": "Your Lisinopril dosage is 10mg taken once daily [1]. This helps manage your blood pressure [2].", "citations": [{"id": 1, "document": "Discharge Prescription", "date": "2026-07-01", "excerpt": "Lisinopril 10mg once daily"}, {"id": 2, "document": "Patient Education", "date": "2026-06-15", "excerpt": "Lisinopril is an ACE inhibitor used to treat hypertension"}], "uncited_statements": []}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Add confidence score per citation
  - Support page/line number references for PDF sources
  - Add citation verification (check claim matches excerpt)
  - Support alternate citation styles (APA, AMA, Vancouver)
---
Format the response with inline citations to source documents.

Response text:
{{ response_text }}

Source documents:
{{ source_documents }}

Return JSON:
```json
{
  "cited_response": "response with inline citations [1], [2]",
  "citations": [
    {"id": 1, "document": "document title", "date": "YYYY-MM-DD", "excerpt": "supporting text"}
  ],
  "uncited_statements": ["statement without source"]
}
```
