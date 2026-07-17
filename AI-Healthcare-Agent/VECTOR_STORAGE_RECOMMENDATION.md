# Vector Storage Recommendation

**Date:** 2026-07-16  
**Author:** Principal Software Architect  
**Status:** Final Recommendation  

---

## Executive Summary

The platform's vector storage strategy has been reviewed end-to-end. The current approach (ChromaDB PersistentClient on local disk) is **not reliable enough for production** on Render free tier, and **not scalable** for future growth.

A complete analysis of 5 architectural options was performed against the criteria: free-tier cost, reliability, future scalability, resume quality, and production readiness.

---

## ✅ Recommended Architecture

**"Index as Derived State" — Ephemeral ChromaDB + Automatic Deterministic Rebuild from PostgreSQL**

> The vector index is treated as derived state, not source of truth.  
> PostgreSQL is the source of truth for all document data.  
> ChromaDB is an ephemeral, rebuildable cache.

### How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                        PostgreSQL (SOURCE OF TRUTH)               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │    reports       │  │    documents     │  │ vector_index   │  │
│  │  · ocr_text      │  │  · file_path     │  │  _state        │  │
│  │  · patient_id    │  │  · metadata      │  │  · report_id   │  │
│  │  · created_at    │  │                  │  │  · status      │  │
│  └──────────────────┘  └──────────────────┘  │  · version     │  │
│                                                └────────────────┘  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  IndexRebuildManager      │
              │  (background task)        │
              │                           │
              │  1. Detect pending/stale  │
              │  2. Load report text      │
              │  3. Run document pipeline │
              │  4. Embed chunks          │
              │  5. Index into ChromaDB   │
              │  6. Update state table    │
              └──────────────────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  ChromaDB EphemeralClient │
              │  (in-memory, rebuildable) │
              │                           │
              │  · No disk persistence    │
              │  · Fully recoverable      │
              │  · Zero data loss risk    │
              └──────────────────────────┘
```

---

## Why This Architecture Wins

### 1. Free-Tier Compatibility ✅
- ChromaDB runs in-process (EphemeralClient) — no separate service needed
- Zero persistent disk required for vector data
- Rend free tier 512MB RAM is sufficient for both backend + in-process ChromaDB
- All data in PostgreSQL (covered by Render free 1GB PostgreSQL or Neon free 500MB)

### 2. Reliability ✅
- **Vector store is fully disposable** — destroy it, restart, rebuild. Zero data loss.
- No single point of failure: if ChromaDB crashes, the app continues serving (RAG returns degraded but auth/CRUD/OCR work)
- PostgreSQL is the source of truth with proper backup (see BACKUP_RECOVERY.md)
- Recovery from total data loss is fully automated

### 3. Future Scalability ✅
- Current abstraction (`BaseVectorStore` ABC + Registry + Factory) allows swapping ChromaDB for pgvector, Pinecone, Qdrant, or Weaviate with **1 config change**
- The `IndexRebuildManager` works regardless of the underlying vector store — it just calls `vector_service.index_chunks()`
- See migration plan below for 1K → 10K → 100K → 1M user scale

### 4. Resume Quality ✅
- Clean architecture decision documented in ADR-028
- No hacky workarounds, no vendor lock-in
- Each component has a single responsibility
- Rebuild is deterministic and verifiable

### 5. Production Readiness ✅
- Health endpoint detects degraded vector store
- App serves during rebuild (graceful degradation)
- State table prevents race conditions during concurrent upload/rebuild
- Embedding model upgrades handled automatically (version mismatch → re-index)

---

## Options Comparison

| Criteria | A: Persistent Disk | B: Ephemeral + Full Rebuild | C: Ephemeral + Incremental | D: pgvector | **E: Hybrid (Recommended)** |
|----------|-------------------|---------------------------|---------------------------|-------------|-----------------------------|
| Free tier | ❌ Unreliable | ✅ Perfect | ✅ Perfect | ✅ Neon | ✅ Perfect |
| Reliability | ❌ Disk can fail | ✅ PostgreSQL is source | ✅ PostgreSQL is source | ✅ ACID | ✅ PostgreSQL is source |
| Startup speed | ✅ Instant | ❌ Slow (full rebuild) | ✅ Fast (incremental) | ✅ Instant | ✅ Fast (incremental) |
| Data loss risk | ❌ High | ✅ Zero | ✅ Zero | ✅ Zero | ✅ Zero |
| Complexity | 🟢 Low | 🟢 Low | 🟡 Medium | 🟡 Medium | 🟡 Medium |
| Recovery time | ❌ Hours (manual) | 🟡 Minutes | 🟢 Seconds | 🟢 Instant | 🟢 Seconds |
| Vendor lock-in | 🟢 Low (ChromaDB) | 🟢 Low (ChromaDB) | 🟢 Low (ChromaDB) | 🟡 Medium (pgvector) | 🟢 Low (ChromaDB) |
| Scalability | ❌ Single node | 🟡 OK to 1K reports | ✅ OK to 10K reports | ✅ OK to 100K | ✅ OK to 10K reports |
| Backup complexity | ❌ Separate ChromaDB backup | 🟢 Free (PG backup covers) | 🟢 Free (PG backup covers) | 🟢 Free (PG backup covers) | 🟢 Free (PG backup covers) |
| Future migration cost | 🟢 Low | 🟢 Low | 🟢 Low | 🟡 Medium | 🟢 Low |

---

## Complete Rebuild Workflow

```
Application Start
│
├─ Step 1: PostgreSQL connection OK
│  └─ Run `alembic upgrade head` (idempotent)
│
├─ Step 2: Initialize ChromaDB (EphemeralClient)
│  └─ Create collection if not exists
│
├─ Step 3: Check vector_index_state table
│  ├─ Compare stored embedding_version with current
│  ├─ If mismatch → mark ALL reports as "stale"
│  └─ Count pending + stale reports
│
├─ Step 4: Health endpoint
│  ├─ If pending_count == 0: /ready → "ready" ✅
│  └─ If pending_count > 0: /ready → "degraded" ⚠️
│      └─ App accepts requests, RAG returns degraded response
│
├─ Step 5: Start background rebuild worker
│  ├─ Batch size: 5 reports
│  ├─ For each report:
│  │   ├─ Load ocr_text from PostgreSQL
│  │   ├─ Run DocumentPipeline.process(...) → chunks
│  │   ├─ Skip if zero chunks
│  │   ├─ Call VectorService.index_chunks(chunks) → index
│  │   └─ UPDATE vector_index_state SET status='indexed'
│  ├─ Between batches: sleep 100ms (avoid API rate limits)
│  ├─ On failure: UPDATE status='failed', log error, continue
│  └─ On complete: /ready → "ready" ✅
│
└─ Step 6: Normal operation
   ├─ On report upload:
   │   ├─ Process through DocumentPipeline
   │   ├─ Index into ChromaDB
   │   ├─ INSERT/UPDATE vector_index_state
   │   └─ Return success
   └─ On report delete:
       ├─ Delete from ChromaDB by report_id
       └─ DELETE FROM vector_index_state
```

### Key Design Properties

| Property | How It's Achieved |
|----------|-------------------|
| **Idempotent** | Pipeline is deterministic; same input → same chunks → same vector IDs |
| **Fail-safe** | Failed reports are marked `failed` in state table; rebuild retries on next startup |
| **Progress-tracked** | `vector_index_state` tracks per-report status; health endpoint exposes aggregate |
| **Rate-limit aware** | Batch processing with configurable delay between batches |
| **Graceful degradation** | App serves during rebuild; RAG falls back to non-vector search when index is empty |
| **Concurrent-safe** | `pending` status prevents double-indexing; row-level locking via `SELECT ... FOR UPDATE` |

---

## Migration Path (No Vendor Lock-In)

```
Now (Phase 1)
Ephemeral ChromaDB + PostgreSQL rebuild
└─ BaseVectorStore ABC: ChromaDBStore

1K–10K reports (Phase 2)
+ Optionally enable PersistentClient on disk
+ Rebuild manager still active (fallback)
└─ No code changes — config change only

10K–100K reports (Phase 3)
+ Implement pgvector adapter
+ Flip provider config: "pgvector"
+ Rebuild manager still active (model upgrades)
└─ New class: PostgresVectorStore(BaseVectorStore)
   └─ Register, configure, done

100K+ reports (Phase 4)
+ Implement Pinecone/Qdrant/Weaviate adapter
+ Dual-write during migration
+ Deprecate ChromaDB adapter
└─ New class: PineconeStore(BaseVectorStore)
   └─ Same pattern. Same interface. Same rebuild manager.
```

At every phase, the fundamental insight holds: **vectors are derived from PostgreSQL data**. The rebuild manager, health checks, and state table are permanent infrastructure that survives any vector store provider change.

---

## Cost Analysis (Free Tier)

| Component | Cost | Notes |
|-----------|------|-------|
| ChromaDB EphemeralClient | $0 | Runs in-process, no infrastructure |
| PostgreSQL (Neon free) | $0 | 500MB storage, 100hr compute/month |
| Gemini Embedding API | $0 | Free tier: 60 RPM, 1,500 RPD |
| Rebuild (10 reports, ~50 chunks) | ~500 API calls | Well within free tier (1,500/day) |
| Rebuild (100 reports, ~500 chunks) | ~5,000 calls | 3.3 days at free tier; upgrade to paid tier or batch over multiple days |

**Recommendation:** For MVP scale (< 100 reports), the free tier covers all rebuild scenarios. If the platform grows, embedding API costs remain negligible ($0.0001/embedding → $0.50 for 5,000 chunks).

---

## Final Verdict

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ✅ RECOMMENDED ARCHITECTURE                                │
│                                                             │
│   Ephemeral ChromaDB + Automatic Deterministic Rebuild       │
│   from PostgreSQL                                            │
│                                                             │
│   "Index as Derived State"                                   │
│                                                             │
│   Rationale:                                                 │
│   ───────────────────────────────────────────────────────     │
│   1. Zero data loss risk — PostgreSQL is source of truth     │
│   2. Free-tier perfect — no disk, no sidecar, no vendor     │
│   3. Self-healing — auto-rebuild from PG on any failure     │
│   4. Future-proof — ABC swap to pgvector/Pinecone = 1       │
│      config change                                           │
│   5. Deterministic — same reports → same vectors every time │
│   6. Production-ready — gracefulegradation during rebuild    │
│   7. Startup-friendly — incremental rebuild in seconds       │
│   8. Resume-worthy — documented, principled, no hacks        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Appendix: Options Rejected

### Option A — Persistent Disk ChromaDB ❌
Rejected because Render free tier cannot guarantee disk persistence. The platform would be one `render deploy` away from total vector data loss with no recovery path.

### Option B — Ephemeral + Full Rebuild ⚠️
Not selected because full rebuild is unnecessary. A state table makes it incremental, which reduces startup delay from minutes to seconds.

### Option D — pgvector ⚠️
Strong alternative, especially on Neon. Rejected for now because it couples vector storage to PostgreSQL schema, making future migrations harder. The `BaseVectorStore` ABC with ChromaDB gives us more freedom. Recommended for Phase 3 if the project grows past 10K reports.
