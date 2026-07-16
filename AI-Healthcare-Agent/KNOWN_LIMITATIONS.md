# Known Limitations — v0.19.0

**Generated:** 2026-07-16  
**Status:** Documented — no fixes required for audit

---

## Architectural Limitations

| # | Limitation | Impact | Workaround | Resolution Path |
|---|-----------|--------|------------|-----------------|
| L-01 | **In-memory memory store** — Conversation memory, LangGraph checkpoint store, and demo service all use in-memory storage | All data lost on process restart — unacceptable for production | None available | Wire Redis or Postgres adapters (scaffolded in memory/stores/future/) |
| L-02 | **Single-tenant MVP** — No hospital/clinic isolation or admin dashboard | Cannot serve multiple organizations | Deploy separate instances per tenant | Multi-tenant PostgreSQL schema + admin API |
| L-03 | **Future AI providers scaffolded only** — OpenAI, Anthropic, Ollama, vLLM providers exist as empty subclasses | Cannot switch LLM without code change | Use Gemini (default) | Wire OpenAI provider (provider exists but needs registration) |
| L-04 | **Future vector stores scaffolded only** — Pinecone, Qdrant, Weaviate adapters exist but untested | Tied to ChromaDB for production | None | Qdrant is the recommended upgrade path |
| L-05 | **Future retrievers scaffolded only** — Hybrid and keyword retrievers exist but untested | Limited to vector-only search | None | Wire hybrid retriever for production |

## Feature Limitations

| # | Limitation | Impact | Workaround |
|---|-----------|--------|------------|
| L-06 | **No email verification** — User registration creates accounts without email confirmation | Unverified accounts; no password reset flow | Manual admin verification |
| L-07 | **Mobile responsiveness** — UI is desktop-first; mobile layouts not optimized | Poor experience on phones | Use in desktop browser |
| L-08 | **No push notifications** — Medicine reminders and emergency alerts are in-app only | Patient must have app open to receive alerts | Not applicable for MVP |
| L-09 | **No background task queue** — Reminder scheduler and adherence monitor are synchronous | May block request thread under load | Celery/Redis task queue |
| L-10 | **Demo data is in-memory** — Seeded demo state resets on restart | Demo user must re-seed after restart | Seed at startup |
| L-11 | **Appointments are skeleton** — Basic CRUD without calendar/scheduling integration | Limited utility for patients | Calendar widget + notification integration |

## Quality Limitations

| # | Limitation | Impact | Workaround |
|---|-----------|--------|------------|
| L-12 | **Zero frontend tests** — No Jest/Vitest tests for React components | Manual QA only; regressions risk | Manual testing of all 14 pages before release |
| L-13 | **No performance baselines** — No captured cold-start, warm-start, or latency metrics | Cannot detect performance regressions | Manual timing; no automated gates |
| L-14 | **No accessibility audit** — No WCAG compliance verification | May not meet accessibility standards | Manual keyboard + screen reader testing |
| L-15 | **Strict CSP may block integrations** — Content-Security-Policy headers may block third-party tools | Integration friction | Tune CSP for deployment environment |
| L-16 | **CSRF disabled in dev mode** — CSRF protection inactive during development | Development-only risk | Enable in production via env config |

## Deployment Limitations

| # | Limitation | Impact | Workaround |
|---|-----------|--------|------------|
| L-17 | **No HTTPS enforcement in app** — TLS termination delegated to reverse proxy | Requires Nginx/load balancer for HTTPS | Use provided Nginx config |
| L-18 | **ChromaDB in Docker** — Vector database runs as container dependency | Additional infrastructure requirement | Can use ChromaDB HTTP client pointing to external instance |
| L-19 | **No database migration automation** — Alembic migrations require manual `alembic upgrade head` | Deployment step must be scripted | Add to CI/CD or entrypoint script |
| L-20 | **No health check for ChromaDB** — Docker health check only configured for PostgreSQL | ChromaDB failure may go undetected | Add health check to chromadb service |

## Security Limitations

| # | Limitation | Impact | Workaround |
|---|-----------|--------|------------|
| L-21 | **No formal HIPAA compliance audit** — Security model follows best practices but not audited | Not suitable for PHI without BAA | Contact maintainer for compliance consultation |
| L-22 | **Rate limiter Redis backend pending** — Redis-based rate limiting is implemented but requires REDIS_URL config | Falls back to in-memory rate limiting | Set REDIS_URL for production |
| L-23 | **No audit log** — Security events (login failures, permission denials) not persistently logged | Cannot investigate security incidents | Future feature (PostgreSQL audit_log table) |

## Documentation Limitations

| # | Limitation | Impact | Workaround |
|---|-----------|--------|------------|
| L-24 | **Duplicate CHANGELOG** — `CHANGELOG.md` and `project_memory/CHANGELOG.md` are out of sync | Version history confusion | Use root CHANGELOG as canonical source |
| L-25 | **project_memory/ docs overlap** — 16 development tracking documents with overlapping content | Navigation overhead | Consolidation recommended for v1.0 |
| L-26 | **No MkDocs/GitHub Pages** — Documentation is file-based only | Less discoverable than web docs | File-based is acceptable for MVP |
