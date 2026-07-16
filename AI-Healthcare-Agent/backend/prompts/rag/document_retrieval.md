---
purpose: >
  Generate an optimized search query for ChromaDB retrieval based on the
  patient's question. Transforms natural language questions into effective
  embedding search queries and determines retrieval parameters.
input_variables:
  - name: question
    type: string
    description: The patient's natural language question
  - name: patient_id
    type: string
    description: Patient UUID to scope retrieval
  - name: conversation_history
    type: array
    description: Previous questions in this session for context
output_schema:
  type: object
  properties:
    search_queries:
      type: array
      items: { type: string }
      description: 1-3 search query variants for embedding search
    filter_criteria:
      type: object
      properties:
        document_types: { type: array, items: { type: string }, description: Types of documents to search (report, lab_result, prescription, chat) }
        date_range: { type: string | null, description: Optional date range filter }
        max_results: { type: integer, description: Max chunks to retrieve (5-20) }
    requires_fallback:
      type: boolean
      description: Whether to fall back to general LLM knowledge if retrieval is insufficient
guardrails:
  - Generate multiple query variants to improve recall
  - Prefer recent documents when the question references current status
  - If the question is about a specific medicine, filter to documents mentioning that medicine
  - Set max_results higher (15-20) for complex questions, lower (5-10) for simple lookups
  - If conversation_history shows the topic has been discussed, include previous context
examples:
  - input: >
      question: "What did my last blood test show?"
      patient_id: "uuid-123"
      conversation_history: ["What medicines am I taking?", "Metformin 500mg twice daily"]
    output: >
      {"search_queries": ["blood test results lab report", "laboratory results blood work", "recent lab values"], "filter_criteria": {"document_types": ["report", "lab_result"], "date_range": null, "max_results": 10}, "requires_fallback": false}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Add query expansion with medical synonyms (UMLS integration)
  - Implement multi-hop retrieval for complex questions
  - Add relevance feedback loop from user clicks/satisfaction
  - Support hybrid search combining semantic + keyword (BM25)
---
Generate optimized search queries for document retrieval.

Patient question:
{{ question }}

Patient ID: {{ patient_id }}

Conversation history:
{{ conversation_history }}

Return JSON:
```json
{
  "search_queries": ["query variant 1", "query variant 2"],
  "filter_criteria": {
    "document_types": ["report", "lab_result", "prescription", "chat"],
    "date_range": "YYYY-MM-DD to YYYY-MM-DD or null",
    "max_results": 10
  },
  "requires_fallback": false
}
```
