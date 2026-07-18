# Automatic Startup Vector Recovery — Phase U.8

> **Date:** 2026-07-18
> **Version:** 1.0.0
> **Status:** ✅ Implemented & Tested

## Problem

On Render Free tier, the filesystem is **ephemeral** — it survives container restarts but is destroyed on **redeploy**. After a redeploy:

1. ChromaDB data at `./chromadb_data` is gone
2. `ChromaDBStore.initialize()` creates a **new empty** collection
3. `RecoveryManager.check_health()` queries `vector_index_state` in PostgreSQL → `indexed_reports = M` (still says "INDEXED")
4. Status = **"healthy"** (no pending, no failed, collection exists)
5. `run_startup_recovery()` skips rebuild
6. All vector searches return **zero results** until manual CLI rebuild

This gap existed before Render Free tier — it would manifest whenever the ChromaDB collection was destroyed independently of PostgreSQL (filesystem corruption, manual deletion). The ephemeral filesystem just makes it certain on every redeploy.

## Root Cause

`check_health()` only looked at `vector_index_state` to determine health — it never compared the actual `document_count` from `ChromaDBStore.health_check()` against the expected `indexed_reports`.

## Solution

### 1. Track actual document count (`health.py`)

Added `actual_document_count: int = 0` field to `VectorHealth` dataclass, included in `to_dict()`.

### 2. Compare counts in check_health (`recovery_manager.py`)

`check_health()` now:
1. Calls `self._vector_service.health_check()` to get actual `document_count`
2. Compares `indexed > actual_document_count` when total > 0
3. Sets status to **"degraded"** on mismatch
4. Sets status to **"rebuilding"** when `rebuild_in_progress` is True

### 3. Mark stale on mismatch + trigger rebuild (`recovery_manager.py`)

`run_startup_recovery()`:
- After initial health check, if `status == "degraded"` with collection missing OR `indexed > actual_document_count`:
  - Initializes collection if missing
  - Calls `_mark_all_indexed_as_stale()` — single UPDATE query resetting INDEXED→STALE
  - Calls `rebuild_all()` to re-index all reports

### 4. New method: `_mark_all_indexed_as_stale()` (`recovery_manager.py`)

Single `UPDATE vector_index_state SET index_status = 'stale' WHERE index_status = 'indexed'` with `db.commit()` and rollback on error.

### 5. API layer updates

- `ready.py`: `/ready` endpoint returns 503 with `"rebuilding"` status during active rebuild
- `monitoring.py`: Response includes `actual_document_count` field in recovery details

### 6. Fixed progress tracking in `rebuild_all()`

The `finally` block in `rebuild_all()` was calling `set_rebuild_progress(in_progress=False)` which reset **all** progress counters to zero (default params). Changed to preserve `total`, `completed`, and `failed` counts so the progress state is accurate after completion.

## Verification

### Startup scenarios

| Scenario | Before U.8 | After U.8 |
|----------|-----------|-----------|
| Fresh deploy (empty DB) | Healthy immediately | ✅ Healthy immediately |
| Redeploy (data in DB) | Healthy → empty search results | ✅ Degraded → auto-rebuilds → Healthy |
| Collection deleted manually | Healthy → empty search results | ✅ Degraded → auto-rebuilds |
| Index partially complete | Reports "pending" correctly | ✅ Unchanged |

### Test results

```
tests/test_vector_recovery.py ... 44 passed in 0.75s
```

| Test Group | Count | Status |
|-----------|-------|--------|
| VectorHealth dataclass | 7 | ✅ All pass |
| RecoveryConfig | 2 | ✅ All pass |
| RecoveryManager (health) | 11 | ✅ All pass |
| RecoveryManager (rebuild) | 8 | ✅ All pass |
| RecoveryManager (verify, cleanup, determine_work) | 5 | ✅ All pass |
| RecoveryManager (startup recovery) | 5 | ✅ All pass |
| RecoveryManager (mark stale) | 3 | ✅ All pass |
| RecoveryManager (progress) | 1 | ✅ All pass |
| RecoveryManager (show_status) | 1 | ✅ All pass |
| Exceptions, IndexStatus | 2 | ✅ All pass |
| **Total** | **44** | **✅ All pass** |

### New U.8 tests (7)

1. `test_to_dict_includes_actual_document_count`
2. `test_degraded_when_indexed_mismatch`
3. `test_rebuilding_status`
4. `test_startup_recovery_marks_stale_on_mismatch`
5. `test_startup_recovery_no_mark_when_matching`
6. `test_mark_all_indexed_as_stale` (+ zero variant + rollback variant)

## Files Changed

| File | Change |
|------|--------|
| `backend/app/vector_recovery/health.py` | Added `actual_document_count` field to `VectorHealth` |
| `backend/app/vector_recovery/recovery_manager.py` | Mismatch detection, stale marking, rebuild trigger, progress fix |
| `backend/app/api/v1/ready.py` | "rebuilding" status handling |
| `backend/app/api/v1/monitoring.py` | `actual_document_count` in response |
| `backend/tests/test_vector_recovery.py` | Complete rewrite — 44 tests, 7 new U.8 tests |

## Regression Risk

- **Low**: The only behavioral change in existing paths is the new `actual_document_count` comparison, which only activates when `indexed > actual_document_count` — this cannot trigger on a healthy system
- `rebuild_all()` progress fix only affects the `finally` block after a rebuild completes — does not affect rebuild logic
