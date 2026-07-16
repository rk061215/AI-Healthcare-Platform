# Roadmap

> **Current Version:** v0.19.0
> **Status:** MVP Complete — Production-Ready

## Completed Milestones

| Milestone | Version | Date | Highlights |
|-----------|---------|------|------------|
| Foundation & Auth | v0.2.0 | Jul 11 | JWT auth, patient/doctor roles, database models |
| Production Data & Prompts | v0.5.0 | Jul 14 | PostgreSQL, Alembic, prompt library |
| AI Architecture | v0.6.0 | Jul 14 | RAG design, AI provider abstraction |
| Document Pipeline | v0.9.0 | Jul 15 | Chunking, embedding, vector store, retrieval, context |
| RAG Engine | v0.10.0 | Jul 15 | Guardrails, citations, confidence scoring |
| Medical QA Agent | v0.11.0 | Jul 15 | Medical question answering |
| Evaluation & Benchmarking | v0.12.0 | Jul 15 | Metrics, hallucination detection, performance |
| Memory Framework | v0.13.0 | Jul 15 | Conversation, preferences, document context |
| Agent Framework | v0.14.0 | Jul 15 | Base agent, lifecycle, executor |
| Tool Calling | v0.15.0 | Jul 15 | Appointment, medication, patient, doctor, report tools |
| LangGraph Runtime | v0.16.0 | Jul 16 | Graph nodes, edges, state, events |
| Clinical Validation | v0.17.0 | Jul 16 | Datasets, benchmarks, optimizers |
| Frontend & Demo | v0.19.0 | Jul 16 | Full UI polish, demo mode, observability, security, deployment |

## Future Roadmap

### Near-Term (v0.20.0 — v0.22.0)

- [ ] **Conversation Memory** — Persistent chat history with session windowing
- [ ] **Patient Chat Agent** — LangGraph-powered Q&A with full memory integration
- [ ] **Real OCR Integration** — End-to-end OCR pipeline with Google Vision + Tesseract
- [ ] **Full CI/CD Pipeline** — GitHub Actions for test, lint, build, deploy

### Medium-Term (v0.23.0 — v0.25.0)

- [ ] **Medicine Reminder Agent** — Automated scheduling and adherence tracking
- [ ] **Emergency Detection Agent** — Real-time symptom triage with alert escalation
- [ ] **Doctor Summary Agent** — AI-generated patient summaries from visit data
- [ ] **Multi-Agent Orchestrator** — Coordinated agent execution via LangGraph supervisor
- [ ] **Appointment Management** — Full scheduling with calendar integration

### Long-Term (v0.26.0+)

- [ ] **Multi-Tenant Support** — Hospital/Clinic isolation with admin dashboard
- [ ] **Production PostgreSQL Store** — Replace in-memory with persistent memory store
- [ ] **Mobile App** — React Native companion for patient notifications
- [ ] **HIPAA Compliance** — Full compliance audit, BAA support, audit logging
- [ ] **Telemedicine Integration** — Video consultation scheduling and EHR integration
- [ ] **Multi-Language Support** — i18n for patient-facing interfaces
- [ ] **Advanced Analytics** — Population health dashboards, readmission prediction

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow and guidelines.
