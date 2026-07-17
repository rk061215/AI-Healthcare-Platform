# ADR-028: Vector Storage Strategy

**Status:** Proposed  
**Date:** 2026-07-16  
**Deciders:** Principal Software Architect  
**Replaces:** Implicit ChromaDB-as-a-service in docker-compose.production.yml  

---

## Context

The platform's AI pipeline depends on vector search for RAG. Currently, ChromaDB is the sole vector store, configured as a PersistentClient writing to local disk. The production deployment audit identified ChromaDB as the biggest remaining risk because:

1. Render free tier cannot run ChromaDB as a separate service (15-min sleep)
2. Persistent disks on Render are shared and can fail
3. No mechanism exists to recover from data loss
4. No backup strategy for vector data
5. The application becomes non-functional if ChromaDB is unavailable

We need a vector storage strategy that is:
- 100% free-tier compatible
- Production-ready
- Self-healing (auto-recover from data loss)
- Deterministic (same documents → same vectors)
- Future-proof (can evolve to pgvector, Pinecone, Qdrant without rewriting)

---

## Current Architecture

```
OCR → Document Pipeline (clean, classify, section, chunk)
    → Embedding Service (text → vector)
    → ChromaDB PersistentClient (local disk)
```

Key properties:
- **Deterministic:** Document pipeline is fully deterministic. Given identical input text and config, identical chunks are produced.
- **Vendor-agnostic abstraction:** `BaseVectorStore` ABC, `VectorStoreRegistry`, `VectorStoreFactory` — adding a new provider requires zero application code changes.
- **Source data in PostgreSQL:** All report text, document metadata, patient data lives in PostgreSQL. Vectors are derived data.
- **Version-aware:** Chunk metadata includes `schema_version`, `embedding_version`, `document_version` — future-proofing for version migrations.

---

## Options Considered

### Option A — Persistent ChromaDB on Render Disk (Current + Fixes)

Run ChromaDB as a persistent process on Render's 1GB disk mount.

**Pros:**
- Works now with minimal changes
- Data survives container restarts
- Fast startup (no rebuild)

**Cons:**
- Render free tier sleeps after 15 min — ChromaDB stops
- Persistent disk is shared with other mounts (ephemeral on redeploy)
- No recovery mechanism if disk corrupts
- No backup strategy for 1GB vector store
- ChromaDB must run in-process (Render can't run sidecar containers on free plan)
- Running ChromaDB in-process + serving HTTP = memory pressure on 512MB free tier
- **Cannot reach production reliability on Render free tier**

**Verdict:** ❌ Rejected — fundamentally unreliable on the only free hosting we can use.

### Option B — Ephemeral ChromaDB + Rebuild from PostgreSQL

Run ChromaDB with `EphemeralClient` (in-memory, no persistence). On every deploy/restart, rebuild the entire vector index from PostgreSQL report data.

**Pros:**
- Perfect free-tier compatibility (no disk needed)
- Deterministic rebuild (identical reports → identical vectors)
- No backup needed (PostgreSQL is the source of truth)
- Version upgrades are free (rebuild with new model/params)
- Lowest operational complexity

**Cons:**
- Slow startup on large datasets (1000 reports × 5 chunks × ~200ms embedding = ~17 min)
- API rate limits on Gemini embedding API during rebuild
- Memory spike during rebuild (all vectors in memory simultaneously)
- Application unavailable during rebuild
- No incremental rebuild (must rebuild everything or nothing)

**Verdict:** ✅ Preferred for scale < 1,000 reports. Rebuild must be async.

### Option C — Ephemeral ChromaDB + Incremental Rebuild from PostgreSQL

Same as Option B, but with tracking of which documents have been indexed via a `vector_index_state` table in PostgreSQL.

**Pros:**
- All benefits of Option B
- Incremental rebuild (only missing/changed documents)
- Fast startup (seconds, not minutes)
- Can parallelize rebuild across multiple workers
- Graceful degradation (app serves requests while rebuilding)

**Cons:**
- More complex (requires state tracking table)
- Embedding model change requires full re-index (detected via `embedding_version` field)
- Document update still requires re-indexing changed docs

**Verdict:** ✅✅ **Recommended** — best balance of reliability, free-tier compatibility, and performance.

### Option D — pgvector in PostgreSQL

Store embeddings directly in PostgreSQL using the `pgvector` extension. Requires Neon (free tier supports pgvector) or self-hosted PostgreSQL with the extension.

**Pros:**
- Single database — no separate vector store to manage
- Transactional consistency (document + vector in same DB)
- ACID guarantees for vector data
- Neon free tier includes pgvector
- PostgreSQL backup covers vectors automatically

**Cons:**
- Neon free tier has 500MB storage limit — vectors are large (768-dim float32 = 3KB/vector; 10K chunks = 30MB; scales but must be monitored)
- pgvector query performance degrades without indexes (IVFFlat/HNSW need tuning)
- Harder to migrate to specialized vector DB later
- Couples vector storage to PostgreSQL schema migrations
- Embedding dimension changes require column migration
- **Vendor lock-in to PostgreSQL+pgvector** (not as easy to swap as ABC provider)

**Verdict:** ⚠️ Strong alternative for scale < 100K vectors. Not recommended now because Option C offers more flexibility and avoids schema coupling.

### Option E — Hybrid: PostgreSQL + Rebuildable ChromaDB

PostgreSQL stores all document data. ChromaDB stores the ephemeral index. A `vector_index_state` table tracks which documents are indexed. On startup, missing documents are rebuilt. Optionally persist ChromaDB to disk when available.

**This is Option C with an optional persistence optimization.**

**Verdict:** ✅✅ **Recommended Architecture** — this is Option C with the fallback to disk persistence when available.

---

## Decision

**Chosen: Option E — Ephemeral ChromaDB + Automatic Deterministic Rebuild from PostgreSQL (a.k.a. "Index as Derived State")**

> The vector index is treated as **derived state**, not source of truth.  
> The source of truth is PostgreSQL (report text + document metadata).  
> The vector store can be destroyed and rebuilt at any time from PostgreSQL.

### Why This Decision

| Requirement | How It's Met |
|-------------|--------------|
| Free tier | ChromaDB EphemeralClient = zero disk cost; no paid services |
| Reliability | Vector store can be completely destroyed and rebuilt — zero data loss |
| Self-healing | Health check detects missing/degraded index → auto-triggers rebuild |
| Deterministic | Same report text + same pipeline config = identical vectors |
| Startup-friendly | Incremental rebuild with state tracking; app serves during rebuild |
| Future-proof | `BaseVectorStore` ABC means swap to pgvector/Pinecone/Qdrant = 1 config change |
| Resume-worthy | Architecture decision is documented and principled |

### Trade-offs Accepted

- **Startup delay on first deploy:** Full rebuild takes ~2s per report (mostly embedding API latency). For 100 reports → ~3 min during which RAG returns degraded results.
- **Gemini API rate limits:** Rebuild respects 60 RPM free tier limit. Mitigated by batching and async rebuild with retry.
- **Memory during rebuild:** Vector batches are processed sequentially, not all at once. Memory stays under 256MB.
- **No cross-report vector operations:** Rebuild is per-report. Deleting a report → remove its vectors. Changing embedding model → full re-index (detected by version mismatch).

---

## Consequences

### Positive
1. **Zero data loss scenario:** If Render deletes the entire disk: restart → rebuild from PostgreSQL → full recovery. No manual intervention.
2. **Backup is free:** PostgreSQL backup covers all data. No separate ChromaDB backup needed.
3. **Free migration:** Switching from ChromaDB to pgvector = implement new `BaseVectorStore` subclass, register it, change config. Vectors rebuild automatically.
4. **Version upgrades:** Changing chunking strategy or embedding model bumps the version → old vectors invalidated → rebuild triggered.
5. **Free-tier hosting:** Works on Render free plan with 512MB RAM and 1GB disk (for uploaded files only).

### Negative
1. **Startup latency:** Full rebuild could take minutes for large datasets. Mitigated by async rebuild with health endpoint returning "degraded" during rebuild.
2. **API costs:** Each rebuild consumes Gemini embedding API calls. At ~$0.0001/embedding, 10,000 chunks = $1/full rebuild. Acceptable.
3. **Race conditions:** If a report is uploaded while a rebuild is in progress, we must ensure it's indexed. Handled by state table (report marked as `pending_index`, picked up by rebuild worker).

---

## Implementation Plan

### New Components

1. **`vector_index_state` table in PostgreSQL:**
   - `report_id` (UUID, FK → reports)
   - `chunk_count` (int)
   - `schema_version` (varchar)
   - `embedding_version` (varchar)
   - `last_indexed_at` (timestamptz)
   - `index_status` (enum: `pending`, `indexed`, `failed`, `stale`)

2. **`IndexRebuildManager` service:**
   - Detects missing/stale entries on startup
   - Rebuilds chunks for each pending/stale report
   - Runs as background task with progress tracking
   - Respects embedding API rate limits
   - Updates `vector_index_state` on completion

3. **Startup health check modification:**
   - `/ready` returns `degraded` during active rebuild
   - `/health` returns `{"status": "healthy", "vector_store": "rebuilding", "progress": "X/Y"}`
   - App serves requests during rebuild (RAG falls back gracefully)

### Modified Components

1. **`VectorService`:**
   - Detect missing collection on startup
   - Trigger rebuild if collection empty or version mismatch
   - Track rebuild progress in shared state

2. **`DocumentPipeline` consumer:**
   - After uploading a report → run pipeline → embed → index → update state table
   - If index is currently rebuilding, mark as `pending` instead

3. **`ChromaDBStore`:**
   - Support both `PersistentClient` (disk) and `EphemeralClient` (memory)
   - Config-driven: `persist_directory=""` → EphemeralClient

### Background Jobs

1. **Startup rebuild job:**
   - Query `vector_index_state` for `pending` or `stale` reports
   - Batch process: load text → chunk → embed → index → update state
   - Runs at most once per app start

2. **Post-upload index job:**
   - After document pipeline completes → index single report → update state

---

## Future Migration Path

### Phase 1 (Now) — Option E with Ephemeral ChromaDB
- Rebuild manager + state table
- EphemeralClient in memory
- Graceful degradation during rebuild

### Phase 2 (1K–10K reports) — Optional Disk Persistence
- Enable PersistentClient when disk available
- Fall back to EphemeralClient + rebuild when disk is lost
- Add periodic full-rebuild cron job for consistency

### Phase 3 (10K–100K reports) — pgvector or Specialized VDB
- Implement pgvector `BaseVectorStore` adapter
- Migrate state table → direct PostgreSQL query
- Compare query latency; keep ChromaDB if competitive

### Phase 4 (100K+ reports) — Pinecone/Qdrant/Weaviate
- Implement cloud provider adapter
- Dual-write during migration
- Deprecate ChromaDB adapter
- The `BaseVectorStore` ABC makes this a configuration change

The rebuild manager remains useful at every stage, because even Pinecone can lose data, and even PostgreSQL needs re-indexing after embedding model changes.

---

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Full rebuild on every deploy | Medium | Startup delay | Incremental rebuild with state tracking |
| Embedding API rate limited during rebuild | High | Slow rebuild | Async rebuild with exponential backoff + batch queuing |
| Report uploaded during rebuild | Medium | Missing vector | State table handles concurrent uploads; `pending` status |
| Memory exhaustion during rebuild | Low | OOM crash | Batch processing: 10 reports at a time, GC between batches |
| Embedding model deprecated | Low | Full re-index | Version field in state table; automatic trigger |
| ChromaDB EphemeralClient bug | Low | Data loss | No data loss — PostgreSQL has source text; rebuild recovers |
| pgvector migration | Low | Effort | ABC pattern: implement adapter, test, flip config |
