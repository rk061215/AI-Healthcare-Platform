# Performance Benchmarks

> **Project:** AI Healthcare Follow-up Assistant  
> **Version:** v1.0.0-rc.1  
> **Last Updated:** 2026-07-16  

---

## 1. Latency Measurement Points

The following diagram illustrates all instrumented measurement points in the pipeline:

```
Request
  │
  ├─ 1. Query Processing          (rag_engine.py:78-80)
  ├─ 2. Query Classification      (rag_engine.py:83-91)
  ├─ 3. Query Rewriting           (rag_engine.py:95-100)
  │
  ├─ 4. Retrieval                 (retrieval_orchestrator.py:71-85)
  ├─ 5. Context Building          (retrieval_orchestrator.py:94-105)
  │
  ├─ 6. Pre-generation Guardrails (rag_engine.py:131-136)
  ├─ 7. Response Generation       (rag_engine.py:149-159)
  ├─ 8. Post-generation Guardrails(rag_engine.py:163-171)
  ├─ 9. Citation Extraction       (rag_engine.py:176-179)
  │
  ├─10. OCR (document pipeline)   (engine.py:43-46)
  ├─11. Embedding (single)        (embedding_service.py:44-48)
  ├─12. Embedding (batch)         (embedding_service.py:50-65)
  ├─13. Graph Node Execution      (graph_executor.py:57-140)
  ├─14. Tool Execution            (tool_executor.py:30-81)
  └─15. Vector Search             (vector_service.py:111-124)
```

### Instrumentation Points Detail

| # | Point | File & Line | Mechanism |
|---|-------|-------------|-----------|
| 1 | Query Processing | `rag_engine.py:78-80` | `time.perf_counter()` |
| 2 | Query Classification | `rag_engine.py:83-91` | `time.perf_counter()` |
| 3 | Query Rewriting | `rag_engine.py:95-100` | Inline, uses processor time internally |
| 4 | Retrieval | `retrieval_orchestrator.py:71-85` | `time.perf_counter()`, stored as `retrieval_time_ms` |
| 5 | Context Building | `retrieval_orchestrator.py:94-105` | `time.perf_counter()`, stored as `build_time_ms` |
| 6 | Pre-generation Guardrails | `rag_engine.py:131-136` | `time.perf_counter()` |
| 7 | Response Generation (LLM) | `rag_engine.py:149-159` | `time.perf_counter()`, stored as `generation_ms` |
| 8 | Post-generation Guardrails | `rag_engine.py:163-171` | `time.perf_counter()` |
| 9 | Citation Extraction | `rag_engine.py:176-179` | `time.perf_counter()` |
| 10 | OCR Processing | `engine.py:43-46` | `time.time()`, stored as `processing_time_ms` |
| 11 | Single Embedding | `embedding_service.py:44-48` | `time.perf_counter()`, stored in `EmbeddingMetadata.duration_ms` |
| 12 | Batch Embedding | `embedding_service.py:50-65` | `time.perf_counter()`, per-text duration |
| 13 | Graph Node Execution | `graph_executor.py:57-140` | `time.time()` in `ExecutionTrace`, stored in `latency_metrics` |
| 14 | Tool Execution | `tool_executor.py:30-81` | `time.time()`, stored as `result.duration_ms` |
| 15 | Vector Search | `vector_service.py:111-124` | Embedded in retrieval timing (point 4) |

---

## 2. Expected Latency Ranges

All values in milliseconds unless noted. Ranges reflect cold-start vs warm-cache scenarios.

| Component | P50 (ms) | P95 (ms) | P99 (ms) | Notes |
|-----------|----------|----------|----------|-------|
| **OCR** (Tesseract, 1 page) | 500–1,500 | 3,000 | 5,000 | Scales linearly with page count; PDF parsing adds overhead |
| **OCR** (Google Vision, 1 page) | 800–2,000 | 4,000 | 6,000 | Network latency dependent |
| **Embedding** (single text) | 50–200 | 500 | 1,000 | Model-dependent (sentence-transformers: 50-100ms; OpenAI: 200-500ms) |
| **Embedding** (batch of 10) | 200–800 | 2,000 | 4,000 | Amortized ~20-80ms per text |
| **Retrieval** (vector search) | 20–100 | 300 | 500 | ChromaDB in-memory: 5-20ms; persisted: 20-100ms; 10k+ vectors: 50-300ms |
| **Context Builder** | 10–50 | 100 | 200 | Tokenization and truncation overhead |
| **LLM Generation** | 500–3,000 | 8,000 | 15,000 | Varies by model (GPT-4o: 2-8s; GPT-4o-mini: 0.5-2s; local: 1-5s) |
| **Graph Execution** (per node) | 100–500 | 2,000 | 5,000 | State transitions, event emission, retries |
| **Total RAG Response** | 1,000–5,000 | 12,000 | 25,000 | Sum of query→classify→retrieve→build→generate→guardrails |
| **Tool Execution** | 200–1,000 | 3,000 | 5,000 | Includes validation, authorization, retry logic |
| **Memory Retrieval** | 5–30 | 80 | 150 | In-memory store; scales with session size |
| **Memory Write** | 2–10 | 30 | 50 | Store + policy checks + optional expiry |
| **Vector Search** (1k vectors) | 10–30 | 50 | 100 | Flat indexing; small collection |
| **Vector Search** (10k vectors) | 30–150 | 300 | 500 | Larger collection; filter overhead |
| **Vector Search** (100k vectors) | 100–500 | 1,000 | 2,000 | Requires approximate nearest neighbor |
| **Pre-grd Guardrails** | 20–100 | 200 | 400 | Content safety check on query + context |
| **Post-grd Guardrails** | 20–100 | 200 | 400 | Content safety check on response |
| **Citation Extraction** | 5–20 | 50 | 100 | Fragment-to-citation mapping |

---

## 3. Benchmark Test Scenarios

### 3.1 Script: `benchmarks/test_ocr_latency.py`

```python
"""Benchmark OCR latency across document types and sizes."""
import time
import asyncio
from pathlib import Path
from statistics import median, stdev

from app.ocr.engine import OcrEngine

ENGINE = OcrEngine()
SAMPLES = {
    "1_page_text": Path("tests/fixtures/1_page_text.pdf"),
    "5_page_report": Path("tests/fixtures/5_page_report.pdf"),
    "20_page_doc": Path("tests/fixtures/20_page_doc.pdf"),
    "50_page_scan": Path("tests/fixtures/50_page_scan.pdf"),
}
WARMUP_ITERATIONS = 3
BENCH_ITERATIONS = 20

def benchmark_ocr(label: str, path: Path):
    timings = []
    for i in range(WARMUP_ITERATIONS):
        ENGINE.process_document(path, "pdf")
    for i in range(BENCH_ITERATIONS):
        start = time.perf_counter()
        result = ENGINE.process_document(path, "pdf")
        elapsed = (time.perf_counter() - start) * 1000
        timings.append(elapsed)
    return {
        "label": label,
        "p50_ms": round(median(timings), 2),
        "p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2),
        "p99_ms": round(sorted(timings)[int(len(timings) * 0.99)], 2),
        "mean_ms": round(sum(timings) / len(timings), 2),
        "stdev_ms": round(stdev(timings), 2),
        "min_ms": round(min(timings), 2),
        "max_ms": round(max(timings), 2),
        "pages": result.pages_processed,
        "confidence": result.confidence,
    }

if __name__ == "__main__":
    for label, path in SAMPLES.items():
        metrics = benchmark_ocr(label, path)
        print(f"[OCR] {metrics}")
```

### 3.2 Script: `benchmarks/test_embedding_latency.py`

```python
"""Benchmark embedding latency for single and batch operations."""
import time
from statistics import median, stdev

from app.embeddings.embedding_service import EmbeddingService

SERVICE = EmbeddingService()
TEXTS_SINGLE = [
    "Patient presents with acute chest pain and shortness of breath.",
    "Lab results show elevated troponin levels indicating myocardial infarction.",
    "The patient has a history of hypertension and type 2 diabetes.",
]
BATCH_SIZES = [1, 5, 10, 25, 50, 100]
WARMUP = 5
ITERATIONS = 30

def benchmark_single_embedding():
    timings = []
    for text in TEXTS_SINGLE:
        for _ in range(WARMUP):
            SERVICE.embed(text)
        for _ in range(ITERATIONS):
            start = time.perf_counter()
            SERVICE.embed(text)
            elapsed = (time.perf_counter() - start) * 1000
            timings.append(elapsed)
    return {
        "p50_ms": round(median(timings), 2),
        "p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2),
        "mean_ms": round(sum(timings) / len(timings), 2),
    }

def benchmark_batch_embedding(batch_size: int):
    texts = [f"Sample clinical text entry number {i} for batch testing." for i in range(batch_size)]
    for _ in range(WARMUP):
        SERVICE.embed_batch(texts)
    timings = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        SERVICE.embed_batch(texts)
        elapsed = (time.perf_counter() - start) * 1000
        timings.append(elapsed)
    per_text = [t / batch_size for t in timings]
    return {
        "batch_size": batch_size,
        "total_p50_ms": round(median(timings), 2),
        "per_text_p50_ms": round(median(per_text), 2),
        "total_p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2),
    }

if __name__ == "__main__":
    print("[Embedding Single]", benchmark_single_embedding())
    for bs in BATCH_SIZES:
        print("[Embedding Batch]", benchmark_batch_embedding(bs))
```

### 3.3 Script: `benchmarks/test_rag_latency.py`

```python
"""Benchmark full RAG pipeline latency with various query types."""
import time
from statistics import median, stdev

from app.rag.rag_engine import RAGEngine
from app.rag.models import RAGRequest

ENGINE = RAGEngine()
QUERIES = {
    "simple": "What medications is the patient currently taking?",
    "moderate": "Summarize the patient's recent lab results and vital signs.",
    "complex": "Compare the patient's HbA1c levels over the last 3 visits and assess diabetes management progress.",
    "guardrail_trigger": "What is the patient's social security number?",
}
WARMUP = 3
ITERATIONS = 15

def benchmark_rag(query_label: str, query_text: str):
    request = RAGRequest(query=query_text, patient_id="benchmark_patient_001")
    for _ in range(WARMUP):
        ENGINE.answer(request)
    timings = {"total": [], "processing": [], "retrieval": [], "generation": [], "context_build": []}
    for _ in range(ITERATIONS):
        resp = ENGINE.answer(request)
        timings["total"].append(resp.processing_time_ms)
    for node in ["retrieval_ms", "generation_ms", "context_build_ms", "query_processing_ms"]:
        # Re-run with metrics capture
        pass
    return {
        "query_label": query_label,
        "total_p50_ms": round(median(timings["total"]), 2),
        "total_p95_ms": round(sorted(timings["total"])[int(len(timings["total"]) * 0.95)], 2),
    }

if __name__ == "__main__":
    for label, query in QUERIES.items():
        print("[RAG]", benchmark_rag(label, query))
```

### 3.4 Script: `benchmarks/test_vector_search_latency.py`

```python
"""Benchmark vector search latency at various corpus sizes."""
import time
from statistics import median, stdev
import numpy as np

from app.vector_store.vector_service import VectorService

SERVICE = VectorService()
CORPUS_SIZES = [100, 500, 1_000, 5_000, 10_000]
K_VALUES = [5, 10, 25, 50]
WARMUP = 5
ITERATIONS = 30

def seed_corpus(size: int):
    """Seed the vector store with `size` random documents."""
    for i in range(size):
        SERVICE.index_text(f"Clinical document seed text number {i} for benchmark purposes.")

def benchmark_search(corpus_size: int, k: int):
    query = "patient blood pressure medication"
    timings = []
    for _ in range(WARMUP):
        SERVICE.search(query, k=k)
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        SERVICE.search(query, k=k)
        elapsed = (time.perf_counter() - start) * 1000
        timings.append(elapsed)
    return {
        "corpus_size": corpus_size,
        "k": k,
        "p50_ms": round(median(timings), 2),
        "p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2),
        "mean_ms": round(sum(timings) / len(timings), 2),
    }

if __name__ == "__main__":
    for size in CORPUS_SIZES:
        seed_corpus(size)
        for k in K_VALUES:
            print("[VectorSearch]", benchmark_search(size, k))
```

### 3.5 Script: `benchmarks/test_memory_latency.py`

```python
"""Benchmark memory service read/write latency."""
import time
from statistics import median, stdev
from uuid import uuid4

from app.memory.memory_service import MemoryService

SERVICE = MemoryService()
SESSION_IDS = [f"bench_session_{i}" for i in range(10)]
WARMUP = 10
ITERATIONS = 100

def benchmark_memory_write():
    timings = []
    session_id = SESSION_IDS[0]
    for _ in range(WARMUP):
        SERVICE.remember(session_id, {"test": "data"}, "clinical_note")
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        SERVICE.remember(session_id, {"test": "data"}, "clinical_note")
        elapsed = (time.perf_counter() - start) * 1000
        timings.append(elapsed)
    return {
        "op": "write",
        "p50_ms": round(median(timings), 2),
        "p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2),
    }

def benchmark_memory_read():
    timings = []
    session_id = SESSION_IDS[1]
    for i in range(50):
        SERVICE.remember(session_id, {"entry": f"data_{i}"}, "clinical_note")
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        SERVICE.recall(session_id, limit=20)
        elapsed = (time.perf_counter() - start) * 1000
        timings.append(elapsed)
    return {
        "op": "read",
        "p50_ms": round(median(timings), 2),
        "p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2),
    }

if __name__ == "__main__":
    print("[Memory]", benchmark_memory_write())
    print("[Memory]", benchmark_memory_read())
```

### 3.6 Script: `benchmarks/test_graph_execution_latency.py`

```python
"""Benchmark LangGraph node execution latency."""
import time
from statistics import median, stdev

from app.langgraph.graph_executor import GraphExecutor
from app.langgraph.graph_state import GraphState, GraphPhase

EXECUTOR = GraphExecutor(node_timeout_ms=30000)

def dummy_node(state: GraphState) -> GraphState:
    state.data["result"] = "processed"
    return state

EXECUTOR.register_node("benchmark_node", dummy_node)
WARMUP = 10
ITERATIONS = 50

def benchmark_graph_execution():
    timings = []
    for _ in range(WARMUP):
        state = GraphState(graph_name="benchmark", phase=GraphPhase.PROCESSING.value)
        EXECUTOR.execute_node("benchmark_node", state, "processing")
    for _ in range(ITERATIONS):
        state = GraphState(graph_name="benchmark", phase=GraphPhase.PROCESSING.value)
        start = time.perf_counter()
        EXECUTOR.execute_node("benchmark_node", state, "processing")
        elapsed = (time.perf_counter() - start) * 1000
        timings.append(elapsed)
    return {
        "p50_ms": round(median(timings), 2),
        "p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2),
        "p99_ms": round(sorted(timings)[int(len(timings) * 0.99)], 2),
    }

if __name__ == "__main__":
    print("[Graph]", benchmark_graph_execution())
```

### 3.7 Script: `benchmarks/test_tool_execution_latency.py`

```python
"""Benchmark tool execution latency."""
import time
from statistics import median, stdev

from app.tools.tool_executor import ToolExecutor
from app.tools.tool_context import ToolContext
from app.tools.base_tool import BaseTool
from app.tools.config import ToolConfig

class MockTool(BaseTool):
    def execute(self, context):
        return self.create_result(data={"status": "ok"})

EXECUTOR = ToolExecutor(MockTool(), ToolConfig(require_validation=False, require_authorization=False))
WARMUP = 10
ITERATIONS = 50

def benchmark_tool():
    timings = []
    for _ in range(WARMUP):
        ctx = ToolContext(user_id="bench", tool_name="mock", action="test")
        EXECUTOR.execute(ctx)
    for _ in range(ITERATIONS):
        ctx = ToolContext(user_id="bench", tool_name="mock", action="test")
        start = time.perf_counter()
        EXECUTOR.execute(ctx)
        elapsed = (time.perf_counter() - start) * 1000
        timings.append(elapsed)
    return {
        "p50_ms": round(median(timings), 2),
        "p95_ms": round(sorted(timings)[int(len(timings) * 0.95)], 2),
    }

if __name__ == "__main__":
    print("[Tool]", benchmark_tool())
```

---

## 4. Performance Targets

| Metric | P50 Target | P95 Target | P99 Target | Alert Threshold |
|--------|-----------|-----------|-----------|-----------------|
| OCR (per page) | ≤1,000 ms | ≤3,000 ms | ≤5,000 ms | >5,000 ms |
| Embedding (single) | ≤100 ms | ≤500 ms | ≤1,000 ms | >1,000 ms |
| Embedding (batch of 10) | ≤500 ms | ≤2,000 ms | ≤4,000 ms | >4,000 ms |
| Query Processing | ≤10 ms | ≤30 ms | ≤50 ms | >100 ms |
| Query Classification | ≤50 ms | ≤200 ms | ≤500 ms | >500 ms |
| Retrieval (vector search) | ≤50 ms | ≤200 ms | ≤500 ms | >500 ms |
| Context Building | ≤30 ms | ≤100 ms | ≤200 ms | >500 ms |
| Guardrails (pre) | ≤50 ms | ≤200 ms | ≤400 ms | >1,000 ms |
| Guardrails (post) | ≤50 ms | ≤200 ms | ≤400 ms | >1,000 ms |
| **LLM Generation** | **≤2,000 ms** | **≤8,000 ms** | **≤15,000 ms** | **>20,000 ms** |
| Citation Extraction | ≤10 ms | ≤50 ms | ≤100 ms | >200 ms |
| **Total RAG Response** | **≤3,000 ms** | **≤10,000 ms** | **≤20,000 ms** | **>25,000 ms** |
| Graph Node Execution | ≤200 ms | ≤2,000 ms | ≤5,000 ms | >5,000 ms |
| Tool Execution | ≤500 ms | ≤3,000 ms | ≤5,000 ms | >5,000 ms |
| Memory Write | ≤10 ms | ≤30 ms | ≤50 ms | >100 ms |
| Memory Read (20 entries) | ≤20 ms | ≤80 ms | ≤150 ms | >200 ms |
| Vector Search (1k corpus) | ≤20 ms | ≤50 ms | ≤100 ms | >200 ms |
| Vector Search (10k corpus) | ≤100 ms | ≤300 ms | ≤500 ms | >1,000 ms |

---

## 5. Summary Table

| Layer | Component | P50 (ms) | P95 (ms) | P99 (ms) | Instrumentation | Health Check |
|-------|-----------|----------|----------|----------|-----------------|-------------|
| **Input** | OCR Engine | 1,000 | 3,000 | 5,000 | `engine.py:43-46` | `OcrJobResult.processing_time_ms` |
| **Input** | Query Processing | 5 | 30 | 50 | `rag_engine.py:78-80` | `RAGMetrics.query_processing_ms` |
| **Input** | Query Classification | 30 | 200 | 500 | `rag_engine.py:83-91` | `RAGMetrics.query_classification_ms` |
| **Embedding** | Single Embedding | 100 | 500 | 1,000 | `embedding_service.py:44-48` | `EmbeddingMetadata.duration_ms` |
| **Embedding** | Batch Embedding | 500 | 2,000 | 4,000 | `embedding_service.py:50-65` | Per-text duration |
| **Retrieval** | Vector Search (1k) | 20 | 50 | 100 | `vector_service.py:111-124` | Implicit via retrieval |
| **Retrieval** | Vector Search (10k) | 100 | 300 | 500 | `vector_service.py:111-124` | Implicit via retrieval |
| **Retrieval** | Context Building | 20 | 100 | 200 | `retrieval_orchestrator.py:94-105` | `RAGMetrics.context_build_ms` |
| **Safety** | Guardrails (pre) | 50 | 200 | 400 | `rag_engine.py:131-136` | `RAGMetrics.guardrail_pre_ms` |
| **Safety** | Guardrails (post) | 50 | 200 | 400 | `rag_engine.py:163-171` | `RAGMetrics.guardrail_post_ms` |
| **Generation** | LLM Generation | 2,000 | 8,000 | 15,000 | `rag_engine.py:149-159` | `RAGMetrics.generation_ms` |
| **Output** | Citation Extraction | 10 | 50 | 100 | `rag_engine.py:176-179` | `RAGMetrics.citation_ms` |
| **Graph** | Node Execution | 200 | 2,000 | 5,000 | `graph_executor.py:57-140` | `GraphState.latency_metrics` |
| **Tools** | Tool Execution | 500 | 3,000 | 5,000 | `tool_executor.py:30-81` | `ToolResult.duration_ms` |
| **Memory** | Memory Write | 5 | 30 | 50 | `memory_service.py:88-125` | Inline timing |
| **Memory** | Memory Read | 15 | 80 | 150 | `memory_service.py:127-145` | Inline timing |
| **End-to-End** | Total RAG Response | 3,000 | 10,000 | 20,000 | `rag_engine.py:189-191` | `RAGMetrics.total_duration_ms` |

---

## 6. Running Benchmarks

```bash
# Run all benchmarks
pytest benchmarks/ -v --benchmark-only

# Run specific benchmark
python -m benchmarks.test_ocr_latency
python -m benchmarks.test_embedding_latency
python -m benchmarks.test_rag_latency
python -m benchmarks.test_vector_search_latency
python -m benchmarks.test_memory_latency
python -m benchmarks.test_graph_execution_latency
python -m benchmarks.test_tool_execution_latency

# Run with historical tracking
pytest benchmarks/ --benchmark-histogram --benchmark-autosave
```

### Continuous Integration

Benchmarks are automatically collected on every RC build:

```yaml
# .github/workflows/benchmarks.yml
benchmark:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    - run: pip install -r requirements.txt
    - run: pytest benchmarks/ --benchmark-json output.json
    - uses: benchmark-action/github-action-benchmark@v1
      with:
        tool: 'pytest'
        output-file-path: output.json
        alert-threshold: '200%'
        fail-on-alert: true
```

---

## 7. Degradation Detection

- **Red/Yellow/Green** status for each metric based on P50/P95 thresholds
- **Trend analysis**: compare last 10 runs for significant deviation (>2σ)
- **Auto-tagging** of RC builds that exceed P99 thresholds (blocking for release)
- **Regression window**: if P95 exceeds baseline by >50% for 3 consecutive runs, file a performance regression ticket
