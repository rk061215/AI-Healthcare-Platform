---
purpose: >
  Compress and deduplicate retrieved document chunks into a concise, relevant
  context window for the LLM. Filters out irrelevant chunks, merges overlapping
  information, and prioritizes the most useful content.
input_variables:
  - name: question
    type: string
    description: Original patient question
  - name: retrieved_chunks
    type: array
    description: Raw chunks from ChromaDB with text, score, and metadata
  - name: max_tokens
    type: integer
    default: 3000
    description: Maximum context tokens for the LLM
output_schema:
  type: object
  properties:
    compressed_context:
      type: string
      description: Deduplicated and prioritized context text
    sources:
      type: array
      items:
        type: object
        properties:
          document_id: { type: string }
          chunk_index: { type: integer }
          relevance: { type: string, enum: [high, medium, low] }
    dropped_chunks:
      type: array
      items:
        type: object
        properties:
          chunk_id: { type: string }
          reason: { type: string, enum: [irrelevant, duplicate, low_score, exceeds_token_limit] }
    total_tokens:
      type: integer
      description: Token count of the compressed context
guardrails:
  - Remove exact duplicate chunks (same text) keeping only the one with highest score
  - Remove chunks with relevance score below 0.5
  - If chunks contradict each other, include both but flag the contradiction
  - Preserve medical terminology accurately; do not paraphrase clinical data
  - If compressed context exceeds max_tokens, prioritize chunks most relevant to the question
  - Include metadata (report date, type) for each source
examples:
  - input: >
      question: "What is my current blood pressure medication?"
      retrieved_chunks: [{"text": "Lisinopril 10mg once daily for hypertension", "score": 0.92, "metadata": {"type": "prescription", "date": "2026-07-01"}}, {"text": "Patient is on Metformin 500mg twice daily", "score": 0.45, "metadata": {"type": "prescription", "date": "2026-07-01"}}]
      max_tokens: 3000
    output: >
      {"compressed_context": "Current blood pressure medication: Lisinopril 10mg once daily (prescribed 2026-07-01)", "sources": [{"document_id": "", "chunk_index": 0, "relevance": "high"}], "dropped_chunks": [{"chunk_id": "", "reason": "irrelevant"}], "total_tokens": 25}
prompt_version: 1.0.0
last_updated: "2026-07-14"
author: AI Healthcare Team
future_improvements:
  - Add query-specific relevance scoring with cross-encoder
  - Implement sliding window for very long documents
  - Add temporal ordering (most recent first)
  - Support multi-query result merging
---
Compress and prioritize retrieved document chunks for the LLM context window.

Question: {{ question }}

Max tokens: {{ max_tokens }}

Retrieved chunks:
{{ retrieved_chunks }}

Return JSON:
```json
{
  "compressed_context": "compressed and relevant context text",
  "sources": [
    {"document_id": "...", "chunk_index": 0, "relevance": "high|medium|low"}
  ],
  "dropped_chunks": [
    {"chunk_id": "...", "reason": "irrelevant|duplicate|low_score|exceeds_token_limit"}
  ],
  "total_tokens": 0
}
```
