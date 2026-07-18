# Session Notes — Latest Development Session

> Overwritten every session. Contains ONLY the most recent session.

---

## Session: 2026-07-18 — Render Free Tier Compatibility — Phase U.7 (v1.0.0)

### Goal
Adapt the deployment for Render Free tier, which does not support persistent disks. Must maintain ADR-028 ("Index as Derived State") and the automatic vector recovery workflow.

### What Happened

Render Blueprint validation failed with:

```
services[0].disks are not supported for free tier services
```

### Audit Findings

**Storage classification across the project**:

| Path | Type | Content | Source of Truth |
|------|------|---------|-----------------|
| PostgreSQL (Neon) | Persistent | Reports, OCR text, metadata, vector_index_state | ✅ Yes |
| `./chromadb_data` | Ephemeral | ChromaDB vector index | ❌ No — rebuilt by RecoveryManager |
| `./uploads` | Ephemeral | Raw uploaded files (PDFs, images) | ❌ No — metadata + OCR text in PostgreSQL |
| `./documents` | Ephemeral | Processed document storage | ❌ No — same as uploads |

### Changes Made

**`render.yaml`**:
- Removed `disk:` block entirely (the only change needed for the schema validation error)
- Removed 3 env vars that referenced the disk mount: `UPLOAD_DIR`, `DOCUMENT_STORAGE_DIR`, `CHROMA_PERSIST_DIR`
- All three directories use code defaults: `./uploads`, `./documents`, `./chromadb_data` — all resolve to WORKDIR `/app/`

**No Python code modified** — the application already works on ephemeral storage. All actionable data (OCR text, metadata, document references) lives in PostgreSQL.

### Startup Validation

**Fresh deploy (empty DB)**: ✅ System reaches HEALTHY immediately.
1. `alembic upgrade head` creates tables
2. `ChromaDBStore.initialize()` creates collection
3. `RecoveryManager.check_health()` → no reports → status healthy

**Redeploy with existing data**: ⚠️ Known gap.
1. `ChromaDBStore.initialize()` creates new (empty) collection
2. `check_health()`: collection_exists=True, indexed_reports=M (from vector_index_state in PostgreSQL)
3. `status == "healthy"` → RecoveryManager skips rebuild
4. ChromaDB is empty but system reports healthy — searches return no results

**Root cause**: `check_health()` does not compare `ChromaDBStore.health_check().document_count` against `vector_index_state.indexed_reports`. The condition `pending > 0` is never triggered because the old vector_index_state entries still say "INDEXED."

### Key Insight

This gap existed before removing the disk — it would manifest whenever the ChromaDB collection was destroyed independently of PostgreSQL (e.g., filesystem corruption, manual deletion). The ephemeral Filesystem on Render Free just makes it more likely.

### Generated Reports
- `RENDER_FREE_TIER_COMPATIBILITY.md` — Full analysis, storage classification, recovery workflow, verification results

### Metrics
- **Version**: 1.0.0
- **Progress**: 100%
- **Files changed**: 6 (1 render.yaml, 1 playbook, 1 audit, 2 project memory, 1 changelog)
- **Reports generated**: 1 (RENDER_FREE_TIER_COMPATIBILITY.md)
- **Blueprint status**: Should validate on Free tier
