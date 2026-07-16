# Benchmark Summary

> Generated: 2026-07-16 12:00 UTC
> Config: clinical_validation_benchmark

## Results

| Metric | Value |
|--------|-------|
| Questions Attempted | 5 |
| Questions Succeeded | 5 |
| Success Rate | 100.0% |

## Retrieval Accuracy (estimated from ground truth evaluation)

| Metric | Value |
|--------|-------|
| Retrieval Recall@5 | 1.0000 |
| Precision@5 | 1.0000 |
| MRR@5 | 1.0000 |
| NDCG@5 | 1.0000 |
| Citation Precision | 0.8000 |
| Citation Recall | 0.6667 |
| Citation F1 | 0.7273 |
| Groundedness | 0.9000 |
| Answer Relevance | 1.0000 |
| Hallucination Rate | 0.1000 |

## Latency (estimated from clinical test runner)

| Metric | Value |
|--------|-------|
| Mean | 0.004 ms |
| Median | 0.002 ms |
| P95 | 0.007 ms |
| P99 | 0.007 ms |
| Min | 0.001 ms |
| Max | 0.007 ms |

## Token Usage

| Metric | Value |
|--------|-------|
| Mean | 100 |
| Total | 500 |

## Optimization Recommendations

### Chunk Size
- Recommended: 512 tokens with 64-token overlap
- Next best: 768 tokens with 128-token overlap

### Retrieval
- Recommended: top_k=5, similarity_threshold=0.7
- Consider reranking for improved precision

### Prompt Strategy
- Current: balanced (relevance × 0.4 + groundedness × 0.4 + hallucination × 0.2)
- Trial required for optimal variant

## Remaining Weaknesses

1. **Limited Dataset Size** — Only 5 QA entries across 3 document types; need 100+ entries for statistical significance
2. **No Real Latency Data** — Benchmarks use mock answer functions; real LLM latency data pending production deployment
3. **Hallucination Rate** — Estimated at 10%; target is <5% for clinical safety
4. **Citation Quality** — F1 of 0.73 is acceptable but should target >0.90 for clinical applications
5. **No Cross-Validation** — Single split limits generalization confidence
