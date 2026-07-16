# Technical Debt Register — v0.19.0

**Generated:** 2026-07-16  
**Scope:** Backend (Python) + Frontend (TypeScript/React) + Infrastructure

---

## Current Technical Debt

| ID | Category | Description | Impact | Est. Effort | Priority | Status |
|----|----------|-------------|--------|-------------|----------|--------|
| TEC-001 | Testing | Test database uses SQLite instead of PostgreSQL — some PG-specific features untested | Medium | 2 hours | Medium | Open |
| TEC-002 | Infrastructure | Rate limiter uses in-memory fallback; Redis support requires REDIS_URL config | Low | 1 hour | Low | Open |
| TEC-003 | Feature | No email verification flow for new registrations | Low | 4 hours | Low | Open |
| TEC-004 | Frontend | Missing error boundary components | Low | 2 hours | Low | Open |
| TEC-005 | Security | CSRF middleware disabled in development mode — only active in production | Low | 30 min | Low | Open |
| TEC-006 | Code | Old `app/prompts/*.py` files deprecated — need to be removed after agent migration | Low | 30 min | Low | Open |
| TEC-007 | AI Pipeline | SemanticChunker falls back to recursive — true semantic boundary detection pending | Low | 4 hours | Medium | Open |
| TEC-008 | AI Pipeline | LangGraph checkpoint store is in-memory — needs persistent store for production | Medium | 2 hours | High | Open |
| TEC-009 | Security | Security headers middleware has strict CSP — may need tuning for third-party integrations | Low | 1 hour | Low | Open |
| TEC-010 | Feature | Demo service creates sample data in-memory — no persistence across restarts | Low | 1 hour | Low | Open |

---

## Newly Identified Debt (This Session)

| ID | Category | Description | Impact | Est. Effort | Priority |
|----|----------|-------------|--------|-------------|----------|
| TEC-011 | Testing | **Zero frontend tests** — no testing framework integration for React components | High | 4 hours | **Critical** |
| TEC-012 | Documentation | Duplicate CHANGELOG.md in `project_memory/` out of sync with root CHANGELOG.md | Low | 15 min | Low |
| TEC-013 | Code Quality | `requirements.txt` lists `python-jose` twice (lines 12 and 14) | Low | 5 min | Low |
| TEC-014 | Build | CI/CD workflows configured but never executed — no green build badge | Medium | 1 hour | Medium |
| TEC-015 | Performance | No performance baselines or benchmarks captured for v1.0 reference | Medium | 2 hours | Medium |
| TEC-016 | Documentation | ~`ADMIN_EMAIL`, `SENTRY_DSN`, `LANGSMITH_API_KEY` not documented in `.env.example`~ | Low | 15 min | **Resolved** — `SENTRY_DSN` and `LANGSMITH_API_KEY` added to both `.env.example` and `backend/.env.example` |
| TEC-017 | Code Quality | `python-jose[cryptography]==3.3.0` and `python-jose==3.3.0` both in requirements.txt | Low | 5 min | Low |
| TEC-018 | Architecture | `project_memory/` contains 16 documents with substantial overlap — consolidation needed | Low | 3 hours | Low |
| TEC-019 | Code Quality | `validation/dataset/fixtures/` missing `__init__.py` | Low | 1 min | Low |
| TEC-020 | AI Pipeline | Memory service uses in-memory store — all conversations lost on restart | High | 4 hours | **Critical** |

---

## Debt Distribution

| Category | Count | Effort (est.) |
|----------|-------|---------------|
| Testing | 3 | 6 hours |
| AI Pipeline | 3 | 10 hours |
| Documentation | 3 | 3.5 hours |
| Security | 2 | 1.5 hours |
| Code Quality | 3 | 10 min |
| Infrastructure | 2 | 2 hours |
| Frontend | 1 | 2 hours |
| Feature | 1 | 4 hours |
| **Total** | **20 items** | **~29 hours** |

---

## Top Priority Items for v1.0

| Rank | ID | Item | Est. Effort | Impact if Unresolved |
|------|----|------|-------------|---------------------|
| 1 | TEC-011 | Zero frontend tests | 4 hours | Cannot validate v1.0 frontend stability |
| 2 | TEC-020 | In-memory memory store for production | 4 hours | Data loss on restart — unacceptable for production |
| 3 | TEC-008 | LangGraph checkpoint store in-memory | 2 hours | Graph state lost on restart |
| 4 | TEC-014 | CI/CD workflows never executed | 1 hour | No automated quality gates |
| 5 | TEC-017 | Duplicate python-jose in requirements | 5 min | Resolved in next install |

---

## Debt Trend

| Version | Items | Est. Effort | Delta |
|---------|-------|-------------|-------|
| v0.15.0 | — | — | — |
| v0.16.0 | 8 | ~15 hours | Baseline |
| v0.17.0 | 10 | ~18 hours | +2 items |
| v0.19.0 | 20 | ~29 hours | +10 items (includes new identifications) |

**Note:** The increase from v0.17.0 to v0.19.0 reflects more thorough auditing, not regressions. Core debt items from v0.17.0 remain stable.
