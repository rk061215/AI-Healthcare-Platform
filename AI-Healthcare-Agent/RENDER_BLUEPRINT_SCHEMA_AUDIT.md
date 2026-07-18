# Render Blueprint Schema Audit

## Summary

Render Blueprint schema validation for Free tier deployment.

**Free Tier Update**: Render Free does not support persistent disks. The `disk:` block was removed entirely. See `RENDER_FREE_TIER_COMPATIBILITY.md` for full analysis.

## Root Cause

Render Blueprint spec defines the `disk` property as a **singular object** (not a list):

```
# CORRECT:
disk:
  name: data
  mountPath: /app/data
  sizeGB: 1

# WRONG:
disks:
  - name: data
    mountPath: /app/data
    sizeGB: 1
```

Additionally, each service supports **at most ONE disk**. The previous config declared three separate disks (uploads, documents, chroma), which violated both constraints.

## Fix Applied (commit `76d367e`)

| Before | After | Rationale |
|--------|-------|-----------|
| `disks:` (list of 3) | `disk:` (single object) | Render Blueprint schema |
| 3 disks: uploads (1GB), documents (1GB), chroma (1GB) | 1 disk: data (1GB) | Render limit of 1 disk per service |
| Mounts: `/app/uploads`, `/app/documents`, `/chroma/chroma` | Mount: `/app/data` | Single mount point |
| `CHROMA_PERSIST_DIR=/chroma/chroma` | `CHROMA_PERSIST_DIR=/app/data/chromadb` | Reflects consolidated path |
| No `UPLOAD_DIR` env var | `UPLOAD_DIR=/app/data/uploads` | Points to subdir on persistent disk |
| No `DOCUMENT_STORAGE_DIR` env var | `DOCUMENT_STORAGE_DIR=/app/data/documents` | Points to subdir on persistent disk |
| `CHROMA_HOST`, `CHROMA_PORT` env vars | Removed | Embedded ChromaDB, not a server |

## Architectural Consistency

Per **ADR-028 (Vector Storage Strategy, Option E)**:

- ChromaDB data lives at `./chromadb_data` (default in `VectorStoreConfig`), which is **outside** the persistent disk mount → **ephemeral**
- On each deploy, ChromaDB is rebuilt deterministically from PostgreSQL via the `RecoveryManager`
- User uploads (`UPLOAD_DIR=/app/data/uploads`) and documents (`DOCUMENT_STORAGE_DIR=/app/data/documents`) **are** on the persistent disk → survive redeploys
- The `CHROMA_PERSIST_DIR` env var documents the intended path for when the code is updated to consume it

## Validation

- `render.yaml` parsed successfully by Python `yaml.safe_load()` — syntax valid
- No `disk:` block (Free tier does not support disks)
- No orphaned env vars referencing `/app/data`
- Blueprint has 0 paid features
- Push to `main` succeeded

## Next Steps

1. [ ] Deploy via Render Dashboard → New → Blueprint → select repo
2. [ ] Set 3 secrets: `DATABASE_URL`, `JWT_SECRET_KEY`, `GEMINI_API_KEY`
3. [ ] Verify `GET /health` returns `{"status": "healthy"}`
4. [ ] Verify `GET /ready` returns `{"status": "ready"}`
