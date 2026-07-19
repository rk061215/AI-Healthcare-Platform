# Query Understanding Module

Advanced query understanding for medical healthcare queries. Part of Phase V Agentic AI Healthcare Assistant.

## Components

### BaseQueryUnderstander (ABC)
Abstract interface for query understanding. Implementations:
- `LLMQueryUnderstander` — uses AI provider (Gemini, OpenAI, etc.) via existing abstraction
- Falls back to rule-based on failure

### MedicalEntityExtractor
Rule-based extraction of medical entities:
- Medication names and dosages
- Lab values and measurements
- Medical conditions
- Symptoms
- Anatomical terms
- Frequencies and routes

### QuestionDecomposer
Splits compound medical questions into atomic sub-questions with intent classification:
- factual, informational, instructional, comparative, diagnostic, etc.

## Usage
```python
from app.query_processing import LLMQueryUnderstander

understander = LLMQueryUnderstander()
result = understander.understand("What is my metformin dosage and when should I take it?")
print(result.intent)  # UnderstandingIntent.factual
print(result.sub_questions)  # [DecomposedQuestion, ...]
print(result.entities)  # [ExtractedEntity, ...]
```
