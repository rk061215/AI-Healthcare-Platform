# v1.0.0 Release Checklist

**Current Version:** v0.19.0  
**Target Version:** v1.0.0

---

## Phase 1: Testing (2 days)

### Backend Tests
- [ ] Run full test suite: `cd backend && pytest -v --cov=app`
- [ ] Verify all 1100+ tests pass with zero failures
- [ ] Generate HTML coverage report
- [ ] Identify modules with coverage <80%
- [ ] Add tests for any uncovered edge cases

### Frontend Tests (NEW — Critical Gap)
- [x] Install and configure Vitest for React components
- [x] Add API service mock tests (at minimum login + chat)
- [x] Run frontend tests: `npm run test:run` → **40/40 passing**

### Integration Tests
- [ ] Test login → dashboard → AI chat flow end-to-end
- [ ] Test document upload → processing → retrieval flow
- [ ] Test demo mode login → scenario selection → guided walkthrough

---

## Phase 2: Security (1 day)

- [ ] Re-run security audit: `python backend/scripts/security_audit.py`
- [ ] Target all 10/10 checks passing
- [ ] Verify JWT_SECRET_KEY is documented for production
- [ ] Verify CORS_ORIGINS is documented for production
- [ ] Confirm no secrets in .env.example or committed files
- [ ] Test rate limiting: rapid requests return 429
- [ ] Test CSRF protection: unauthenticated POST returns 403
- [ ] Test file upload validation: invalid file types rejected
- [ ] Verify security headers in API responses
- [x] Add `SENTRY_DSN`, `LANGSMITH_API_KEY` to `backend/.env.example` (root `.env.example` already had them)

---

## Phase 3: Infrastructure (1 day)

### Docker
- [ ] Verify `docker compose -f docker/docker-compose.yml up -d` starts clean
- [ ] Verify `docker compose -f docker/docker-compose.production.yml up -d` starts clean
- [ ] Add health check for ChromaDB service
- [ ] Verify PostgreSQL + ChromaDB connect on first startup
- [ ] Test Alembic migration: `alembic upgrade head` runs without errors

### CI/CD
- [ ] Push to GitHub and trigger CI workflows
- [ ] Verify backend CI passes (lint + type check + tests)
- [ ] Verify frontend CI passes (lint + type check + build)
- [x] Add frontend `test` job to CI workflow

### Environment
- [ ] Verify all required env vars are documented
- [ ] Create production .env template with only production vars
- [ ] Test with minimal env (only required vars)

---

## Phase 4: Performance (1 day)

- [ ] Capture cold start time (docker compose up → API ready)
- [ ] Capture warm API response time for `/health`
- [ ] Capture chat response time (typical query)
- [ ] Capture document upload + processing time
- [ ] Capture peak memory usage under load
- [ ] Document baselines in PERFORMANCE_BASELINES.md

---

## Phase 5: Documentation (1 day)

- [ ] Verify CHANGELOG.md has complete v0.19.0 entry
- [ ] Verify all markdown files reference v0.19.0 (or v1.0.0)
- [ ] Consolidate or remove duplicate project_memory/CHANGELOG.md
- [x] Add __init__.py to `validation/dataset/fixtures/`
- [x] Fix duplicate python-jose and httpx in requirements.txt
- [ ] Verify all README links work
- [ ] Add real screenshots to assets/ and uncomment gallery
- [ ] Verify CONTRIBUTING.md references are correct

---

## Phase 6: Deployment (1 day)

- [ ] Deploy to staging (Render or Railway)
- [ ] Verify health endpoint returns OK
- [ ] Verify frontend loads and communicates with backend
- [ ] Test demo mode on live deployment
- [ ] Verify environment variables work in production
- [ ] Test file upload via public URL
- [ ] Test AI chat via public URL
- [ ] Verify Prometheus metrics endpoint accessible
- [ ] Verify structured logging output

---

## Phase 7: Portfolio Polish (0.5 day)

- [ ] Record 2-3 minute demo video
- [ ] Add live demo link badge to README
- [ ] Update repository description and topics on GitHub
- [ ] Merge ROADMAP.md into README or keep separate
- [ ] Verify GitHub social preview image

---

## Phase 8: Release (0.5 day)

- [ ] Update version to v1.0.0 in all files:
  - [ ] CHANGELOG.md
  - [ ] RELEASE_CANDIDATE_REPORT.md
  - [ ] project_memory/CURRENT_STATUS.md
  - [ ] project_memory/PROJECT_OVERVIEW.md
  - [ ] README.md
- [ ] Create annotated tag: `git tag -a v1.0.0 -m "v1.0.0 - AI Healthcare Platform"`
- [ ] Push tag: `git push origin v1.0.0`
- [ ] Create GitHub Release with release notes
- [ ] Archive pre-release reports (this file and others)

---

## Go/No-Go Criteria

### MUST pass before v1.0.0:

- [ ] All 1100+ backend tests pass
- [ ] Frontend smoke tests pass (minimum 5)
- [ ] Security audit passes 8/10+
- [ ] Docker compose starts cleanly
- [ ] CI/CD workflows pass
- [ ] Staging deployment operational

### SHOULD pass before v1.0.0:

- [ ] Performance baselines captured
- [ ] Duplicate CHANGELOG consolidated
- [ ] All markdown version references consistent
- [ ] Screenshots added to README

### NICE TO HAVE for v1.0.0:

- [ ] Demo video recorded
- [ ] Live demo badge in README
- [ ] GitHub Pages documentation
- [ ] MkDocs documentation site

---

## Estimated Remaining Effort

| Phase | Estimated Time | Assigned To |
|-------|---------------|-------------|
| Testing | 2 days | — |
| Security | 1 day | — |
| Infrastructure | 1 day | — |
| Performance | 1 day | — |
| Documentation | 1 day | — |
| Deployment | 1 day | — |
| Portfolio Polish | 0.5 day | — |
| Release | 0.5 day | — |
| **Total** | **8 days** | **—** |
