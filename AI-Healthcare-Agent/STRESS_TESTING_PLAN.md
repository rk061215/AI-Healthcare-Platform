# Stress Testing Plan

> **Project:** AI Healthcare Follow-up Assistant  
> **Version:** v1.0.0-rc.1  
> **Last Updated:** 2026-07-16  

---

## 1. Multiple Concurrent Uploads

### Test Methodology

Upload 10, 25, 50, 100 PDF files concurrently via the document pipeline endpoint. Each file is a 3-page clinical report (~150KB). Measure end-to-end throughput (files/minute), per-file processing latency, and error rate.

### Expected Behavior

- All files are processed through OCR → chunking → embedding → indexing pipeline
- Pipeline scales horizontally; queue depth grows but no files are dropped
- Under heavy load, processing time per file increases due to resource contention

### Success Criteria

| Metric | Target |
|--------|--------|
| Success rate | 100% (no dropped files) |
| Throughput (10 files) | ≥20 files/min |
| Throughput (50 files) | ≥50 files/min |
| Throughput (100 files) | ≥80 files/min |
| Max processing time per file | ≤60s (P99) |
| Zero data corruption after indexing | Verified by spot-check |

### Resource Monitoring

| Resource | Warning | Critical |
|----------|---------|----------|
| CPU | >70% | >90% |
| Memory (process) | >2GB RSS | >4GB RSS |
| Disk I/O | >100 MB/s | >500 MB/s |
| DB (ChromaDB) size growth | Monitored per batch | <500 MB/hour |
| Thread pool queue depth | >50 | >200 |

### Gradation

```
Level 1:  5 files  (3 iterations, baseline)
Level 2: 10 files  (3 iterations)
Level 3: 25 files  (3 iterations)
Level 4: 50 files  (3 iterations)
Level 5: 100 files (1 iteration, max load)
```

### Script: `stress_tests/test_concurrent_uploads.py`

```python
"""Stress test: multiple concurrent file uploads."""
import asyncio
import time
from pathlib import Path
from statistics import median, stdev
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.ocr.engine import OcrEngine

ENGINE = OcrEngine()
FIXTURE = Path("tests/fixtures/3_page_report.pdf")
LEVELS = [5, 10, 25, 50, 100]

def process_file(path: Path) -> dict:
    start = time.perf_counter()
    result = ENGINE.process_document(path, "pdf")
    elapsed = (time.perf_counter() - start) * 1000
    return {
        "status": result.status,
        "elapsed_ms": elapsed,
        "confidence": result.confidence,
    }

def stress_concurrent_uploads(count: int) -> dict:
    files = [FIXTURE] * count
    timings = []
    errors = 0
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=count) as executor:
        futures = {executor.submit(process_file, f): f for f in files}
        for future in as_completed(futures):
            result = future.result()
            timings.append(result["elapsed_ms"])
            if result["status"] != "completed":
                errors += 1
    total_elapsed = time.perf_counter() - start
    throughput = count / (total_elapsed / 60)
    return {
        "level": count,
        "total_time_s": round(total_elapsed, 2),
        "throughput_files_per_min": round(throughput, 2),
        "p50_ms": round(median(timings), 2),
        "p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2),
        "errors": errors,
    }

if __name__ == "__main__":
    for level in LEVELS:
        print("[UploadStress]", stress_concurrent_uploads(level))
```

---

## 2. Large PDF Processing

### Test Methodology

Process PDFs of 10, 25, 50, 100, 200 pages. Each page contains mixed text and tables simulating clinical reports. Measure: total processing time, per-page latency, peak memory usage, and OCR accuracy degradation.

### Expected Behavior

- Processing time scales linearly with page count
- Memory usage increases with page count but remains bounded
- OCR confidence remains stable across page count (no ±5% degradation)
- No crashes for documents up to 200 pages

### Success Criteria

| Metric | Target |
|--------|--------|
| Time per page (Tesseract) | ≤2s/page |
| Time per page (Google Vision) | ≤3s/page |
| Peak memory (100 pages) | ≤1.5GB RSS |
| Peak memory (200 pages) | ≤2.5GB RSS |
| Confidence degradation (10→200 pg) | <5% drop |
| Success rate | 100% |

### Resource Monitoring

| Resource | Warning | Critical |
|----------|---------|----------|
| Process RSS memory | >1GB (50pg) | >2GB (100pg) |
| Temp disk usage | >500MB | >2GB |
| PDF rasterization CPU | >60s | >120s |

### Gradation

```
Level 1: 10 pages  (baseline)
Level 2: 25 pages
Level 3: 50 pages
Level 4: 100 pages
Level 5: 200 pages (stress limit)
```

### Script: `stress_tests/test_large_pdf_processing.py`

```python
"""Stress test: processing large PDF documents."""
import time
import tracemalloc
from pathlib import Path

from app.ocr.engine import OcrEngine

ENGINE = OcrEngine()
PDF_SIZES = [10, 25, 50, 100, 200]

def stress_large_pdf(page_count: int) -> dict:
    path = Path(f"tests/fixtures/large_{page_count}p.pdf")
    import os
    if not path.exists():
        return {"page_count": page_count, "error": "Fixture not found"}

    # Measure peak memory during processing
    tracemalloc.start()
    start = time.perf_counter()
    result = ENGINE.process_document(path, "pdf")
    elapsed = (time.perf_counter() - start) * 1000
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "page_count": page_count,
        "total_time_ms": round(elapsed, 2),
        "time_per_page_ms": round(elapsed / page_count, 2),
        "peak_memory_mb": round(peak / 1024 / 1024, 2),
        "confidence": result.confidence,
        "pages_processed": result.pages_processed,
        "text_length": result.text_length,
        "status": result.status,
    }

if __name__ == "__main__":
    for pages in PDF_SIZES:
        print("[LargePDF]", stress_large_pdf(pages))
```

---

## 3. Large Conversation Histories

### Test Methodology

Simulate conversations with 10, 50, 100, 200, 500 turns. Each turn includes a query and an LLM-generated response (summarized context). Measure: memory retrieval latency, context window token count, total request latency, and summarization trigger behavior.

### Expected Behavior

- Memory retrieval time grows slowly with turn count (O(log n) for indexed stores)
- At `summarization_threshold` turns, automatic summarization is triggered
- Context window utilization increases but stays within configured limits
- Latency increases primarily due to larger context being passed to LLM

### Success Criteria

| Metric | Target |
|--------|--------|
| Memory retrieval (100 turns) | ≤100ms P95 |
| Memory retrieval (500 turns) | ≤300ms P95 |
| Context token count | ≤max_tokens setting |
| Summarization accuracy | Manual review ≥90% |
| Request latency increase (10→500 turns) | <3x |

### Resource Monitoring

| Resource | Warning | Critical |
|----------|---------|----------|
| Session memory size | >5MB | >20MB |
| Memory store entry count | >1000/session | >5000/session |
| Token usage per request | >8k | >16k |

### Gradation

```
Level 1: 10 turns  (baseline)
Level 2: 50 turns
Level 3: 100 turns (common real-world max)
Level 4: 200 turns
Level 5: 500 turns (extreme)
```

### Script: `stress_tests/test_large_conversations.py`

```python
"""Stress test: large conversation histories."""
import time
from statistics import median, stdev

from app.memory.memory_service import MemoryService
from app.memory.config import MemoryConfig

CONFIG = MemoryConfig(
    max_memories_per_session=1000,
    enable_pruning=True,
    summarization_threshold=50,
)
SERVICE = MemoryService(config=CONFIG)
SESSION_ID = "stress_large_conv_session"
TURN_COUNTS = [10, 50, 100, 200, 500]

def simulate_session(turns: int) -> dict:
    for i in range(turns):
        SERVICE.extract_from_chat(
            session_id=SESSION_ID,
            query=f"What is the patient's status at turn {i}?",
            answer=f"The patient is stable, vital signs normal at turn {i}.",
            turn_number=i,
        )

    timings = []
    for _ in range(10):
        start = time.perf_counter()
        results = SERVICE.recall(SESSION_ID, limit=20)
        elapsed = (time.perf_counter() - start) * 1000
        timings.append(elapsed)

    session_count = SERVICE.get_session_count(SESSION_ID)
    return {
        "turns": turns,
        "memory_entries": session_count,
        "retrieval_p50_ms": round(median(timings), 2),
        "retrieval_p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2),
    }

if __name__ == "__main__":
    for turns in TURN_COUNTS:
        print("[LargeConv]", simulate_session(turns))
```

---

## 4. Concurrent API Requests

### Test Methodology

Send 10, 25, 50, 100, 200 simultaneous RAG API requests using `asyncio` or threaded clients. Each request uses a unique patient ID to prevent cache effects. Measure: request throughput, P50/P95/P99 latency, error rate, and resource saturation.

### Expected Behavior

- System degrades gracefully: latency increases linearly with concurrency
- No HTTP 500 errors under expected load
- Connection pool and thread pool do not exhaust
- Rate limiting kicks in at configured thresholds (if enabled)

### Success Criteria

| Metric | Target |
|--------|--------|
| Success rate (50 concurrent) | 100% |
| Success rate (200 concurrent) | ≥99% |
| Latency increase (10→50 req) | <3x |
| Error rate (4xx/5xx) | <1% |
| Mean throughput (100 concurrent) | ≥30 req/min |

### Resource Monitoring

| Resource | Warning | Critical |
|----------|---------|----------|
| CPU | >70% | >90% |
| Memory (process) | >2GB RSS | >4GB RSS |
| Open file descriptors | >1000 | >2000 |
| Active database connections | >10 | >25 |
| Connection pool wait time | >500ms | >2s |

### Gradation

```
Level 1: 10 concurrent  (baseline)
Level 2: 25 concurrent
Level 3: 50 concurrent  (target max)
Level 4: 100 concurrent (stress)
Level 5: 200 concurrent (breaking point)
```

### Script: `stress_tests/test_concurrent_api.py`

```python
"""Stress test: concurrent RAG API requests."""
import asyncio
import time
from statistics import median, stdev

import aiohttp

BASE_URL = "http://localhost:8000/api/v1"
CONCURRENCY_LEVELS = [10, 25, 50, 100, 200]

async def send_query(session: aiohttp.ClientSession, patient_id: str) -> dict:
    start = time.perf_counter()
    try:
        async with session.post(
            f"{BASE_URL}/rag/answer",
            json={
                "query": "Summarize the patient's current medications and dosages.",
                "patient_id": patient_id,
            },
            timeout=aiohttp.ClientTimeout(total=60),
        ) as resp:
            elapsed = (time.perf_counter() - start) * 1000
            data = await resp.json()
            return {
                "status": resp.status,
                "elapsed_ms": elapsed,
                "error": None,
            }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return {"status": 0, "elapsed_ms": elapsed, "error": str(e)}

async def stress_concurrent_api(concurrency: int) -> dict:
    connector = aiohttp.TCPConnector(limit=concurrency, limit_per_host=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            send_query(session, f"stress_patient_{i}")
            for i in range(concurrency)
        ]
        start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        total_elapsed = time.perf_counter() - start

    timings = [r["elapsed_ms"] for r in results if r["status"] == 200]
    errors = [r for r in results if r["status"] != 200]
    throughput = concurrency / (total_elapsed / 60) if total_elapsed > 0 else 0

    return {
        "concurrency": concurrency,
        "total_time_s": round(total_elapsed, 2),
        "throughput_req_per_min": round(throughput, 2),
        "success_count": len(timings),
        "error_count": len(errors),
        "p50_ms": round(median(timings), 2) if timings else 0,
        "p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2) if timings else 0,
    }

if __name__ == "__main__":
    for level in CONCURRENCY_LEVELS:
        result = asyncio.run(stress_concurrent_api(level))
        print("[ConcurrentAPI]", result)
```

---

## 5. Repeated Memory Retrieval Cycles

### Test Methodology

Perform 100, 500, 1000, 5000 consecutive memory write + read cycles on the same session. Measure: per-operation latency, memory store growth, pruning behavior, and degradation over time.

### Expected Behavior

- Initial operations are fast (<10ms); latency may increase as store grows
- Pruning triggers at `max_memories_per_session` threshold
- Expired entries are automatically cleaned up
- After pruning, memory count stabilizes around `pruning_max_count`

### Success Criteria

| Metric | Target |
|--------|--------|
| Max memory entries after pruning | ≤`pruning_max_count` |
| Write latency (cycle 1000) | ≤50ms P95 |
| Read latency (cycle 1000) | ≤100ms P95 |
| Zero memory leaks | RSS stable after pruning |
| Pruning accuracy | All low-importance entries removed |

### Resource Monitoring

| Resource | Warning | Critical |
|----------|---------|----------|
| Memory store entry count | >`pruning_max_count` × 2 | >`pruning_max_count` × 5 |
| Per-session memory (RSS) | >10MB | >50MB |
| Pruning CPU time | >5s per trigger | >30s per trigger |

### Gradation

```
Level 1: 100 cycles  (baseline)
Level 2: 500 cycles
Level 3: 1000 cycles (target)
Level 4: 5000 cycles (endurance)
```

### Script: `stress_tests/test_memory_endurance.py`

```python
"""Stress test: repeated memory read/write cycles."""
import time
from statistics import median, stdev

from app.memory.memory_service import MemoryService
from app.memory.config import MemoryConfig

CONFIG = MemoryConfig(
    max_memories_per_session=100,
    enable_pruning=True,
    pruning_max_count=80,
    pruning_importance_threshold=0.3,
    enable_expiry_policy=False,
    enable_retention_policy=False,
)
SERVICE = MemoryService(config=CONFIG)
SESSION_ID = "stress_memory_endurance"
CYCLE_COUNTS = [100, 500, 1000, 5000]

def stress_memory_cycles(cycles: int) -> dict:
    write_timings = []
    read_timings = []

    for i in range(cycles):
        # Write
        start = time.perf_counter()
        SERVICE.remember(
            SESSION_ID,
            {"data": f"cycle_{i}", "importance": 0.1 if i % 5 == 0 else 0.8},
            "clinical_note",
        )
        write_timings.append((time.perf_counter() - start) * 1000)

        # Read every 10th cycle to measure read performance
        if i % 10 == 0:
            start = time.perf_counter()
            SERVICE.recall(SESSION_ID, limit=20)
            read_timings.append((time.perf_counter() - start) * 1000)

    current_count = SERVICE.get_session_count(SESSION_ID)
    return {
        "cycles": cycles,
        "final_entry_count": current_count,
        "pruning_triggered": current_count <= CONFIG.pruning_max_count,
        "write_p50_ms": round(median(write_timings), 2),
        "write_p95_ms": round(sorted(write_timings)[int(len(write_timings) * 0.95)], 2),
        "read_p50_ms": round(median(read_timings), 2) if read_timings else 0,
        "read_p95_ms": round(sorted(read_timings)[int(len(read_timings) * 0.95)], 2) if read_timings else 0,
    }

if __name__ == "__main__":
    for cycles in CYCLE_COUNTS:
        SERVICE.clear(SESSION_ID)
        print("[MemoryEndurance]", stress_memory_cycles(cycles))
```

---

## 6. Large Vector Collections

### Test Methodology

Populate the vector store with 100, 1,000, 5,000, 10,000, 50,000, 100,000 document vectors. Measure similarity search latency at various `k` values (5, 10, 25, 50). Include metadata-filtered searches. Measure index build time and storage growth.

### Expected Behavior

- Search latency increases with corpus size (O(n) for flat indexes, O(log n) for HNSW/IVF)
- Metadata filtering adds constant overhead per search
- Index construction time scales linearly with corpus size
- Memory usage proportional to vector dimensions × count × 4 bytes

### Success Criteria

| Metric | Target |
|--------|--------|
| Search latency (10k vectors, k=10) | ≤200ms P95 |
| Search latency (100k vectors, k=10) | ≤1,000ms P95 |
| Index build (10k vectors) | ≤30s |
| Index build (100k vectors) | ≤5min |
| Storage (10k vectors, 768d) | ≤100MB |
| Filtered search overhead | ≤50ms |

### Resource Monitoring

| Resource | Warning | Critical |
|----------|---------|----------|
| Process memory (100k vectors) | >1GB | >3GB |
| ChromaDB storage | >500MB | >2GB |
| Index build CPU | >2min (10k) | >10min (100k) |
| Search CPU per query | >100ms | >500ms |

### Gradation

```
Level 1: 100 vectors    (baseline)
Level 2: 1,000 vectors
Level 3: 5,000 vectors
Level 4: 10,000 vectors (target max production)
Level 5: 50,000 vectors (stress)
Level 6: 100,000 vectors (breaking point)
```

### Script: `stress_tests/test_large_vector_collection.py`

```python
"""Stress test: large vector collection search performance."""
import time
from statistics import median, stdev

from app.vector_store.vector_service import VectorService

SERVICE = VectorService()
COLLECTION_NAME = "stress_test_collection"
CORPUS_SIZES = [100, 1_000, 5_000, 10_000, 50_000, 100_000]
K_VALUES = [5, 10, 25, 50]
QUERY_TEXTS = [
    "patient blood pressure medication hypertension",
    "lab results hemoglobin a1c glucose levels",
    "chest pain cardiac evaluation troponin",
]

def seed_and_benchmark(corpus_size: int, k: int) -> dict:
    # Seed collection (incremental)
    for i in range(corpus_size):
        SERVICE.index_text(
            f"Clinical note number {i}: Patient presents with symptoms and history.",
            metadata={"patient_id": f"stress_pat_{i % 100}", "source": "stress_test"},
        )

    timings = []
    for query in QUERY_TEXTS:
        for _ in range(5):  # warmup
            SERVICE.search(query, k=k)
        for _ in range(20):
            start = time.perf_counter()
            results = SERVICE.search(query, k=k)
            elapsed = (time.perf_counter() - start) * 1000
            timings.append(elapsed)

    return {
        "corpus_size": corpus_size,
        "k": k,
        "p50_ms": round(median(timings), 2),
        "p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2),
        "mean_ms": round(sum(timings) / len(timings), 2),
        "results_count": len(results),
    }

if __name__ == "__main__":
    for size in CORPUS_SIZES:
        for k in K_VALUES:
            print("[LargeVector]", seed_and_benchmark(size, k))
        print(f"--- Completed corpus size: {size} ---")
```

---

## 7. Running Stress Tests

```bash
# Run all stress tests sequentially
python -m stress_tests.test_concurrent_uploads
python -m stress_tests.test_large_pdf_processing
python -m stress_tests.test_large_conversations
python -m stress_tests.test_concurrent_api
python -m stress_tests.test_memory_endurance
python -m stress_tests.test_large_vector_collection

# Run a specific stress test at maximum level
python -m stress_tests.test_concurrent_api --max-level 200

# Run with resource monitoring (Windows)
# Use Performance Monitor (perfmon) or:
# python -m stress_tests.test_large_pdf_processing &
# Get-Process python* | Select-Object Id, WorkingSet64, CPU
```

### Prerequisites

- All stress tests require a running instance of the backend application
- Test fixtures must exist in `tests/fixtures/`:
  - `3_page_report.pdf`
  - `large_10p.pdf`, `large_25p.pdf`, `large_50p.pdf`, `large_100p.pdf`, `large_200p.pdf`
- Vector store must be empty or use a dedicated test collection
- Database should be backed up before running destructive tests

### Reporting

Each stress test outputs JSON to stdout. For CI, redirect to files:

```bash
python -m stress_tests.test_concurrent_api > reports/stress_concurrent_api.json
```

Collect and aggregate:

```bash
python -c "
import json, glob
results = []
for f in glob.glob('reports/stress_*.json'):
    with open(f) as fh:
        results.append(json.load(fh))
print(json.dumps(results, indent=2))
"
```

### Pass/Fail Criteria

A stress test level passes if:
1. Success rate meets or exceeds the target for that level
2. No unrecoverable errors (crash, deadlock, data corruption)
3. Resource usage stays below Critical thresholds
4. System recovers to baseline within 30s after test completion

---

## 8. Combined Stress Scenario (Optional)

For the most realistic assessment, run a combined stress scenario:

```
Phase 1 (5 min):  5 concurrent uploads + 10 API requests/min + 10-turn conversations
Phase 2 (10 min): 10 concurrent uploads + 25 API requests/min + 50-turn conversations  
Phase 3 (15 min): 25 concurrent uploads + 50 API requests/min + 100-turn conversations
Phase 4 (10 min): 10 concurrent uploads + 25 API requests/min + reduce to 50-turn
Phase 5 (5 min):  cool down, verify system recovery
```

This validates that the system can handle mixed workloads and return to baseline after load is removed.
