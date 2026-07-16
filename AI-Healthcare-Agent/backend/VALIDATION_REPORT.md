# Clinical Validation Report

> Generated: 2026-07-16 12:00 UTC

## Overview

| Metric | Value |
|--------|-------|
| Datasets Validated | 1 (sample_golden_qa) |
| Total Entries | 5 |
| Errors | 0 |
| Warnings | 0 |
| Valid | True |

## Dataset Details

### sample_golden_qa
- Version: 1.0.0
- Documents: 3
- Entries: 5
- Valid: True
- Errors: 0
- Warnings: 0

## Document Types Coverage

| Document Type | Entries | Status |
|---------------|---------|--------|
| CBC Report | 2 | ✅ |
| Lipid Profile | 2 | ✅ |
| Prescription | 1 | ✅ |

## Difficulty Distribution

| Level | Count |
|-------|-------|
| Easy | 3 |
| Medium | 1 |
| Hard | 1 |

## Category Distribution

| Category | Count |
|----------|-------|
| lab_result | 3 |
| diagnosis | 1 |
| medication | 1 |

## Validation Module Health

| Module | Files | Tests | Status |
|--------|-------|-------|--------|
| Dataset Management | 6 | 46 | ✅ All pass |
| Benchmark System | 5 | 32 | ✅ All pass |
| Optimization | 4 | 13 | ✅ All pass |
| Evaluation | 4 | 19 | ✅ All pass |
| **Total** | **19** | **110** | **✅ All pass** |

## Recommendations

1. Expand the golden QA dataset to cover all 10 document types with at least 5 entries each
2. Add clinically verified ground truth from domain experts for high-confidence evaluation
3. Implement cross-validation folds for more robust benchmark results
4. Add synthetic data generation for edge cases (abnormal values, missing data, contradictory information)
