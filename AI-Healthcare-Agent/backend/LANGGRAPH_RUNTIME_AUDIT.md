# LangGraph Runtime Audit

## Status: COMPLETED — Phase L

### Runtime Architecture

```
load_memory → medical_qa → tool_selector ──need_tool?──→ tool_executor
                                   │                         │
                                   │                   (fall through)
                                   │                         │
                                   └──no_tool──→ need_retrieval?
                                                    │
                                          ┌─────────┴──────────┐
                                          ▼                    ▼
                                     retriever          response_generator
                                          │
                                          ▼
                                   context_builder
                                          │
                                          ▼
                                   response_generator
                                          │
                                          ▼
                                   persist_memory
```

### Module Structure

| Module | Lines | Coverage | Description |
|--------|-------|----------|-------------|
| `config.py` | 17 | 100% | Graph configuration |
| `exceptions.py` | 10 | 100% | Graph-specific exception hierarchy |
| `graph_state.py` | 93 | 100% | Strongly-typed state with trace, metrics, services |
| `graph_context.py` | 31 | 65% | Dependency injection context |
| `graph_events.py` | 49 | 100% | EventBus with typed events |
| `graph_checkpoint.py` | 71 | 93% | InMemory checkpoint store + manager |
| `graph_metrics.py` | 54 | 100% | Per-graph metrics collection |
| `graph_registry.py` | 29 | 97% | Graph class registry |
| `graph_factory.py` | 23 | 57% | Graph instantiation |
| `graph_executor.py` | 89 | 91% | Node execution with retries/timeout |
| `graph_runtime.py` | 93 | 82% | BaseGraph ABC with lifecycle |
| `graphs/medical_qa_graph.py` | 66 | — | Full medical QA pipeline |
| `nodes/*.py` (8 files) | — | 15-90% | Single-responsibility node functions |
| `edges/*.py` (2 files) | — | — | Conditional routing edges |

### Key Design Decisions

1. **LangGraph is ONLY orchestration** — Business logic stays in Agent Framework, Memory Framework, Tool Framework, RAG Engine
2. **Strongly-typed GraphState** — Full dataclass with all pipeline fields
3. **Injected services via `state.services` dict** — No DI framework coupling
4. **Node functions are idempotent** — Accept and return GraphState
5. **EventBus for observability** — Subscribe to graph/node lifecycle events
6. **CheckpointManager for state snapshots** — Create/restore mid-execution

### Test Results

- **New LangGraph tests**: 81/81 passing (100%)
- **Existing integration tests**: 182/182 passing (unmodified)
- **Total**: 263/263 passing

### Files Created (13 new)

- `app/langgraph/graph_events.py`
- `app/langgraph/graph_checkpoint.py`
- `app/langgraph/graph_metrics.py`
- `app/langgraph/graph_registry.py`
- `app/langgraph/graph_factory.py`
- `app/langgraph/graph_executor.py`
- `app/langgraph/graph_runtime.py`
- `app/langgraph/graphs/medical_qa_graph.py`
- `app/langgraph/nodes/*.py` (8 files)
- `app/langgraph/edges/*.py` (2 files)
- `tests/test_langgraph/*.py` (9 files)

### Recommendations

1. Register `MedicalQAGraph` in `GraphRegistry` at app startup with `get_global_registry().register("medical_qa", MedicalQAGraph)`
2. Wire real services (memory_service, agent_executor, tool_service, rag_engine, context_builder) into `state.services` before executing
3. In production, swap `InMemoryCheckpointStore` for a persistent store
4. Add `app/langgraph/__init__.py` to the auto-import chain at app boot
