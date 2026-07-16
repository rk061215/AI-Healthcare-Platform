# Prompt Library Index

> Central registry of all prompt templates in the Prompt Library.
> All prompts live as standalone Markdown files under `backend/prompts/`.
> Code should load prompts via `PromptManager` (`app/prompts/manager.py`).

**Total prompts:** 18
**Categories:** 6
**Last updated:** 2026-07-15

---

## medical/ (3 prompts)

Clinical data extraction from medical reports and prescriptions.

| # | File | Purpose | Version |
|---|------|---------|---------|
| 1 | `medical/report_analysis.md` | Extract structured clinical data (disease, medicines, follow-up) from OCR text | 1.0.0 |
| 2 | `medical/medicine_extraction.md` | Parse individual medicine entries with dosage, route, timing | 1.0.0 |
| 3 | `medical/diagnosis_check.md` | Verify extracted diagnosis is consistent with report text evidence | 1.0.0 |

## chat/ (3 prompts)

Patient-facing conversational AI prompts.

| # | File | Purpose | Version |
|---|------|---------|---------|
| 4 | `chat/patient_chat.md` | System prompt for patient chat agent — role, rules, context-aware Q&A | 2.0.0 |
| 5 | `chat/medication_qa.md` | Focused medication Q&A — dosage, side effects, interactions | 1.0.0 |
| 6 | `chat/follow_up.md` | Generate follow-up questions to encourage patient engagement | 1.0.0 |

## emergency/ (3 prompts)

Emergency symptom triage and escalation.

| # | File | Purpose | Version |
|---|------|---------|---------|
| 7 | `emergency/symptom_triage.md` | Classify symptom urgency as LOW, MEDIUM, or HIGH | 2.0.0 |
| 8 | `emergency/risk_assessment.md` | Secondary review to determine escalation need | 1.0.0 |
| 9 | `emergency/escalation.md` | Generate structured doctor alert and patient message | 1.0.0 |

## summary/ (3 prompts)

Clinical summarization for doctors and care teams.

| # | File | Purpose | Version |
|---|------|---------|---------|
| 10 | `summary/doctor_summary.md` | Concise post-discharge clinical summary for the doctor | 2.0.0 |
| 11 | `summary/appointment_summary.md` | Pre-appointment brief highlighting changes since last visit | 1.0.0 |
| 12 | `summary/weekly_report.md` | Weekly patient status report for care coordination | 1.0.0 |

## rag/ (3 prompts)

Retrieval-Augmented Generation pipeline prompts.

| # | File | Purpose | Version |
|---|------|---------|---------|
| 13 | `rag/document_retrieval.md` | Generate optimized search queries for ChromaDB retrieval | 1.0.0 |
| 14 | `rag/context_compression.md` | Compress and deduplicate retrieved chunks for LLM context | 1.0.0 |
| 15 | `rag/citation_format.md` | Format inline citations with source references | 1.0.0 |

## system/ (3 prompts)

Global system configuration and safety layers.

| # | File | Purpose | Version |
|---|------|---------|---------|
| 16 | `system/system_config.md` | Core assistant identity, capabilities, limitations, ethics | 3.0.0 |
| 17 | `system/guardrails.md` | Content safety filter — blocks harmful or misleading outputs | 2.0.0 |
| 18 | `system/output_formatter.md` | JSON schema validation and repair for LLM outputs | 1.0.0 |

---

## Usage

### Low-level (core loader — direct access)
```python
from app.core.prompt_loader import PromptLoader
prompt = PromptLoader.load("medical/report_analysis")
rendered = prompt.render(text=ocr_text)
```

### RAG Prompt Management System (recommended)
```python
from app.prompts import PromptManager

mgr = PromptManager()

# Load and render a prompt
rendered = mgr.render("rag/document_retrieval", question=user_question)

# List available prompts
rag_prompts = mgr.list_prompts(category="rag")
all_prompts = mgr.list_prompts()

# Get version metadata
version = mgr.get_version("medical/report_analysis")

# Preload all prompts into cache
mgr.preload_all()

# Cache management
mgr.invalidate_cache("rag/document_retrieval")  # single prompt
mgr.invalidate_cache()                           # all prompts
```

### RAG Prompt Modules (app/prompts/)

| Module | Class | Purpose |
|--------|-------|---------|
| `app/prompts/cache.py` | `PromptCache` | TTL+LRU cache with hit/miss stats |
| `app/prompts/loader.py` | `RAGPromptLoader` | `PromptVersion`, `RAGPrompt` with version tracking |
| `app/prompts/manager.py` | `PromptManager` | Central registry: discovery, querying, preloading |

## Migration Status

| Old location | New location | Status |
|-------------|-------------|--------|
| `app/prompts/medical_report.py` | `prompts/medical/report_analysis.md` | ✅ Migrated |
| `app/prompts/patient_chat.py` | `prompts/chat/patient_chat.md` | ✅ Migrated |
| `app/prompts/emergency.py` | `prompts/emergency/symptom_triage.md` | ✅ Migrated |
| `app/prompts/doctor_summary.py` | `prompts/summary/doctor_summary.md` | ✅ Migrated |
| `app/agents/medical_agent/prompts.py` | `prompts/medical/medicine_extraction.md` | ✅ Migrated |
