# AI Architecture

> Complete architectural design for the AI-powered healthcare follow-up assistant.
> This document governs ALL future AI implementation. No code should be written
> until the architecture decisions here are understood and approved.
>
> **Status:** Design Phase (pre-implementation)
> **Last Updated:** 2026-07-14
> **Author:** AI Healthcare Team

---

## Table of Contents

1. [Agent Responsibilities](#1-agent-responsibilities)
2. [LangGraph State Design](#2-langgraph-state-design)
3. [Node Design](#3-node-design)
4. [Edges & Routing](#4-edges--routing)
5. [Memory Architecture](#5-memory-architecture)
6. [Checkpointing & Persistence](#6-checkpointing--persistence)
7. [Error Recovery](#7-error-recovery)
8. [Retry Strategy](#8-retry-strategy)
9. [Fallback LLM](#9-fallback-llm)
10. [Tool Calling](#10-tool-calling)
11. [Structured Outputs & JSON Schemas](#11-structured-outputs--json-schemas)
12. [Hallucination Prevention](#12-hallucination-prevention)
13. [Medical Safety](#13-medical-safety)
14. [Cost Optimization](#14-cost-optimization)
15. [Latency Optimization](#15-latency-optimization)
16. [Streaming Strategy](#16-streaming-strategy)
17. [Prompt Versioning](#17-prompt-versioning)
18. [Evaluation Strategy](#18-evaluation-strategy)

---

## 1. Agent Responsibilities

The system has **6 agents**, each with a clearly bounded responsibility. No agent
crosses into another agent's domain. The Orchestrator determines which agent(s)
to invoke based on the incoming request.

### 1.1 Medical Report Agent

| Attribute | Design |
|-----------|--------|
| **Purpose** | Extract structured clinical data from OCR-processed medical reports and prescriptions |
| **Input** | OCR text, patient_id, report_id |
| **Output** | Structured medicine list, disease, follow-up date, doctor instructions |
| **Owns** | `medicines` and `reports` table writes for extraction results |
| **Does NOT do** | Diagnose, interpret lab values, or generate clinical opinions |
| **Trigger** | POST `/api/v1/reports/upload` completion event |
| **LLM Model** | `gpt-4o-mini` (fast, cheap, sufficient for extraction) |

### 1.2 Patient Chat Agent

| Attribute | Design |
|-----------|--------|
| **Purpose** | Answer patient questions about medications, reports, appointments, and post-discharge care |
| **Input** | Patient question, patient_id, chat history |
| **Output** | Natural language response with source citations |
| **Owns** | `chat_history` table writes |
| **Does NOT do** | Diagnose, change medications, or override doctor instructions |
| **Trigger** | POST `/api/v1/chat/message` |
| **LLM Model** | `gpt-4o` (higher quality for conversational nuance) |

### 1.3 Emergency Detection Agent

| Attribute | Design |
|-----------|--------|
| **Purpose** | Classify symptom urgency (LOW/MEDIUM/HIGH) and escalate when necessary |
| **Input** | Free-text symptom description, patient_id, patient condition context |
| **Output** | Risk level, analysis, recommendations, escalation decision |
| **Owns** | `emergency_alerts` table writes |
| **Does NOT do** | Diagnose specific diseases, provide treatment advice |
| **Trigger** | POST `/api/v1/emergency/check` |
| **LLM Model** | `gpt-4o` (safety-critical, needs best reasoning) |

### 1.4 Medicine Reminder Agent

| Attribute | Design |
|-----------|--------|
| **Purpose** | Generate medication schedules, track adherence, detect missed doses |
| **Input** | Patient ID, active medicines list, adherence log history |
| **Output** | Schedule entries, adherence statistics, missed dose alerts |
| **Owns** | `adherence_logs` table reads/writes; reminder scheduling |
| **Does NOT do** | Use LLMs for scheduling (rule-based) — only for patient-facing messages |
| **Trigger** | APScheduler cron (every 15 min) + on-demand adherence check |
| **LLM Model** | None for scheduling; `gpt-4o-mini` for reminder message generation |

### 1.5 Doctor Summary Agent

| Attribute | Design |
|-----------|--------|
| **Purpose** | Generate concise clinical summaries for doctors from aggregated patient data |
| **Input** | Patient ID, date range (default: since last summary) |
| **Output** | Structured clinical summary with adherence metrics, risk flags, recommendations |
| **Owns** | Summary generation only — does not write to DB (displayed in dashboard) |
| **Does NOT do** | Modify patient data, prescribe, or override doctor decisions |
| **Trigger** | Doctor requests summary (GET `/api/v1/doctors/{id}/patients/{id}/summary`) |
| **LLM Model** | `gpt-4o` (clinical accuracy demands highest quality) |

### 1.6 Orchestrator

| Attribute | Design |
|-----------|--------|
| **Purpose** | Route incoming requests to the correct agent, manage multi-agent workflows |
| **Input** | Request type + payload |
| **Output** | Dispatched to appropriate agent; aggregates multi-agent results |
| **Responsibility** | Agent selection, request validation, response formatting, error handling |
| **Does NOT do** | Any AI work itself — pure routing and coordination |
| **LLM Model** | None (pure routing logic) |

### Responsibility Boundaries (Non-Negotiable)

```
Agent A's output ──> Agent B's input is ALLOWED ONLY when explicitly designed:

  Medical Report Agent ──> Medicine Reminder Agent (extracted medicines feed scheduler)
  Emergency Agent ──> Doctor Summary Agent (alerts appear in summary)
  Chat Agent ──> Emergency Agent (chat context triggers escalation check)

The following CROSS-BOUNDARY flows are FORBIDDEN:
  ✗ Chat Agent writing to medicines table
  ✗ Emergency Agent modifying appointment schedules
  ✗ Any agent diagnosing a disease
  ✗ Any agent providing treatment recommendations
```

---

## 2. LangGraph State Design

### 2.1 State Pattern

All agents use a **shared top-level schema** with agent-specific extensions.
State is defined as `TypedDict` for type safety, not `dataclass` or `BaseModel`.

```python
# Base fields present in ALL agent states
class BaseAgentState(TypedDict):
    request_id: str                        # UUID for tracing
    patient_id: str                        # Always present when patient context exists
    user_role: str                         # "patient" | "doctor" | "system"
    errors: list[dict]                     # Accumulated error log [{node, message, timestamp}]
    retry_count: int                       # Current retry attempt number
    started_at: str                        # ISO timestamp
    metadata: dict                         # Open field for trace context, env flags
```

### 2.2 Per-Agent State Schemas

Each agent extends the base with its own fields. These are the **complete** state
definitions that must be implemented.

**Medical Report Agent State**
```python
class MedicalReportState(BaseAgentState):
    # Input
    raw_text: str
    report_id: str
    report_type: str                       # "prescription" | "lab_result" | "discharge_summary"

    # Processing
    extracted_data: dict | None            # Parsed JSON result from LLM
    medicines: list[dict] | None           # Extracted medicines sub-list
    validation_status: str | None          # "pending" | "validated" | "failed"
    diagnosis_consistency: dict | None     # Output from diagnosis_check prompt

    # Output
    extraction_confidence: float | None    # 0.0 - 1.0
    requires_human_review: bool            # Flag for low-confidence extractions
```

**Patient Chat Agent State**
```python
class ChatAgentState(BaseAgentState):
    # Input
    question: str
    chat_history: list[dict]               # Previous messages [{role, content}]

    # RAG
    search_queries: list[str]              # Generated search queries
    retrieved_chunks: list[dict]           # Raw chunks from ChromaDB
    compressed_context: str | None         # After context compression

    # Processing
    draft_response: str | None             # Raw LLM output before guardrails
    guardrail_check: dict | None           # Guardrail evaluation result

    # Output
    final_response: str | None             # After guardrails + formatting
    sources: list[dict]                    # Citations [{document_id, chunk, relevance}]
    requires_escalation: bool              # True → invoke Emergency Agent
```

**Emergency Detection Agent State**
```python
class EmergencyAgentState(BaseAgentState):
    # Input
    symptoms: str
    patient_condition: str | None          # Known conditions from DB
    recent_alerts: list[dict]              # Last 30 days of alerts

    # Processing
    triage_result: dict | None             # Output from symptom_triage prompt
    risk_assessment: dict | None           # Output from risk_assessment prompt

    # Output
    risk_level: str | None                 # "LOW" | "MEDIUM" | "HIGH"
    analysis: str | None                   # Clinical reasoning
    recommendations: list[str] | None      # Patient-facing recommendations
    disclaimer: str | None
    escalate: bool                         # True → trigger escalation flow
    escalation_alert: dict | None          # Doctor alert + patient message
```

**Medicine Reminder Agent State**
```python
class ReminderAgentState(BaseAgentState):
    # Input
    mode: str                              # "check" | "generate" | "adherence_report"
    medicines: list[dict]                  # Active medicines with schedule info

    # Processing
    schedule: list[dict] | None            # Computed dose schedule for today
    missed_doses: list[dict] | None        # Doses past scheduled time not logged
    adherence_stats: dict | None           # {overall_rate, missed_count, trend}

    # Output
    reminders: list[dict] | None           # [{medicine, time, message, channel}]
    adherence_summary: str | None          # LLM-generated patient message
```

**Doctor Summary Agent State**
```python
class SummaryAgentState(BaseAgentState):
    # Input
    date_range: tuple[str, str] | None     # (start_date, end_date), defaults to last 7 days

    # Data aggregation
    patient_data: dict | None              # Demographics, condition, discharge date
    medicines: list[dict] | None           # Active medicines + adherence rates
    recent_symptoms: list[dict] | None     # From chat + alerts
    alerts: list[dict] | None              # Recent emergency alerts
    chat_summary: str | None               # Condensed AI interaction summary
    reports: list[dict] | None             # Recent reports with key findings

    # Output
    summary: dict | None                   # Structured clinical summary
    adherence_metrics: dict | None         # {overall_rate, missed_doses, improving}
    risk_flags: list[str] | None           # Flags for doctor attention
    next_review_date: str | None           # Suggested follow-up window
```

### 2.3 State Immutability Rules

1. **Nodes receive a copy** of the state dict — they must return a new dict, not mutate in place
2. **`errors` list is append-only** — once added, errors are never removed
3. **`retry_count` resets to 0** when entering a new top-level request (Orchestrator manages this)
4. **`extracted_data` is write-once** — after the extraction node sets it, no other node may overwrite
5. **State must be JSON-serializable** at all times for checkpointing

---

## 3. Node Design

### 3.1 Node Naming Convention

```
{agent}_{action}    # e.g., medical_extract_entities, chat_generate_response
```

Every node name is a snake_case verb phrase that describes exactly what it does.

### 3.2 Node Interface

Every node follows this exact interface:

```python
async def node_name(state: AgentState, context: NodeContext) -> AgentState:
    """One-sentence description of what this node does.

    Args:
        state: The current agent state (TypedDict).
        context: Runtime dependencies (LLM client, DB session, prompt loader, etc.).

    Returns:
        Updated state with the node's output fields populated.

    Raises:
        NodeExecutionError: On unrecoverable failure.
        NodeSkipException: When the node determines it should be skipped.
    """
```

### 3.3 Node Categories

| Category | Pattern | Example | Error Handling |
|----------|---------|---------|---------------|
| **LLM Call** | Build prompt → Call LLM → Parse response | `medical_extract_entities` | Retry on timeout, fallback model on auth error |
| **DB Query** | Query DB → Transform → Store in state | `summary_aggregate_data` | Return partial data, log error |
| **Validation** | Check state → Pass/Fail → Set flags | `medical_validate_extraction` | Set `validation_status = "failed"`, continue |
| **Routing** | Evaluate state → Return next node name | `chat_should_escalate` | Default to safe path (no escalation) |
| **Transform** | Transform state data → Set new fields | `rag_compress_context` | Skip compression, use raw chunks |
| **Output** | Format response → Apply guardrails → Write to DB | `chat_format_output` | Return safe default response |

### 3.4 Complete Node Inventory

**Medical Report Agent** (5 nodes)
```
extract_entities          LLM Call  — Run report_analysis prompt
extract_medicines         LLM Call  — Run medicine_extraction prompt for detailed parsing
validate_extraction       Validation — Run diagnosis_check prompt, set confidence score
check_consistency         Validation — Cross-reference extracted disease with medicine list
store_results             DB Query  — Write medicines/report data to database
```

**Patient Chat Agent** (5 nodes)
```
retrieve_context          DB Query  — Query ChromaDB, get relevant chunks
compress_context          Transform — Run context_compression prompt on chunks
generate_response         LLM Call  — Run patient_chat prompt with context + history
check_guardrails          Validation — Run guardrails prompt on draft response
format_output             Transform — Run output_formatter, add citations, write to DB
should_escalate           Routing   — Check requires_escalation flag → Emergency Agent
```

**Emergency Detection Agent** (5 nodes)
```
analyze_symptoms          LLM Call  — Run symptom_triage prompt
assess_risk               LLM Call  — Run risk_assessment prompt with patient history
decide_escalation         Routing   — Evaluate risk_level + history → escalate boolean
generate_alert            LLM Call  — Run escalation prompt (only if escalate=True)
store_alert               DB Query  — Write emergency_alert to database
```

**Medicine Reminder Agent** (4 nodes)
```
check_schedule            DB Query  — Query active medicines, compute due doses
detect_missed_doses       DB Query  — Compare schedule against adherence_logs
generate_reminders        Transform — Create reminder messages (rule-based)
update_adherence_stats    DB Query  — Calculate adherence percentage, write summary
```

**Doctor Summary Agent** (4 nodes)
```
aggregate_data            DB Query  — Pull patient data, medicines, symptoms, alerts, chat, reports
compress_chat_history     Transform — Condense long chat histories (LLM-based summarization)
generate_summary          LLM Call  — Run doctor_summary prompt with aggregated data
format_summary            Transform — Structure output, flag risks, compute review date
```

**Orchestrator** (3 nodes)
```
classify_request          Routing   — Determine which agent(s) to invoke
dispatch_agent            Transform — Parse state, call agent.invoke(), merge results
format_response           Output    — Build API response from agent output
```

---

## 4. Edges & Routing

### 4.1 Edge Types

| Edge Type | Description | Implementation |
|-----------|-------------|---------------|
| **Sequential** | Always go to next node | `workflow.add_edge("node_a", "node_b")` |
| **Conditional** | Choose next node based on state | `workflow.add_conditional_edges("node", router_func)` |
| **Parallel fan-out** | Execute multiple nodes simultaneously | `workflow.add_parallel_edges("node", [targets])` |
| **Self-loop** | Retry the same node | Router function returns the same node name |
| **Error edge** | Redirect to error handler | Conditional edge on `state["errors"]` |

### 4.2 Per-Agent Edge Maps

**Medical Report Agent**
```
extract_entities ──[if raw_text empty]──> END (error)
                └──[if ok]──> extract_medicines
                                  │
                                  ▼
                            validate_extraction
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
            check_consistency              END (skip)
                    │
                    ▼
              store_results ──> END
```

**Patient Chat Agent**
```
retrieve_context ──> compress_context ──> generate_response
                                               │
                                               ▼
                                         check_guardrails
                                               │
                              ┌────────────────┴────────────────┐
                              ▼                                 ▼
                        format_output                      END (blocked)
                              │
                              ▼
                        should_escalate ──[if true]──> Emergency Agent
                              │
                              ▼
                             END
```

**Emergency Detection Agent**
```
analyze_symptoms ──> assess_risk ──> decide_escalation
                                          │
                          ┌───────────────┴───────────────┐
                          ▼                               ▼
                    generate_alert                   store_alert (LOW risk)
                          │                               │
                          ▼                               ▼
                    store_alert                          END
                          │
                          ▼
                         END
```

**Doctor Summary Agent**
```
aggregate_data ──> compress_chat_history ──> generate_summary ──> format_summary ──> END
```

**Medicine Reminder Agent**
```
check_schedule ──> detect_missed_doses ──> generate_reminders ──> update_adherence_stats ──> END
```

### 4.3 Conditional Router Functions

Router functions follow this pattern:

```python
def route_after_validation(state: MedicalReportState) -> str:
    """Route to consistency check or end if extraction failed."""
    if state.get("validation_status") == "failed":
        return "end"
    return "check_consistency"
```

All router functions:
- Return a **string** matching a node name or `END`
- Are **pure functions** (no async, no I/O)
- Must have a **default return** (safe path)
- Are registered via `workflow.add_conditional_edges("node", router_func, {name: name})`

### 4.4 Multi-Agent Routing (Orchestrator Level)

```python
def route_to_agent(request_type: str) -> str:
    """Determine which agent handles this request type."""
    routing_map = {
        "report_upload": "medical_agent",
        "chat_message": "chat_agent",
        "emergency_check": "emergency_agent",
        "doctor_summary": "summary_agent",
        "adherence_check": "reminder_agent",
    }
    return routing_map.get(request_type, "error_handler")
```

Cross-agent handoffs:
- Chat Agent → Emergency Agent: When `requires_escalation` flag is set, Orchestrator
  spawns an Emergency Agent with the chat context pre-populated.
- Medical Agent → Reminder Agent: When new medicines are extracted, Orchestrator
  triggers a Reminder Agent run to update the schedule.

---

## 5. Memory Architecture

### 5.1 Memory Types

| Memory Type | Scope | Storage | Duration | Implementation |
|-------------|-------|---------|----------|---------------|
| **Conversation History** | Per chat session | `chat_history` table | Persistent | Windowed (last 20 messages), loaded by Chat Agent |
| **Patient Context** | Per patient | `patients` + related tables | Persistent | Loaded at agent start by DB query nodes |
| **Session State** | Per request | LangGraph checkpoint | Until request completes | Automatic — handled by StateGraph |
| **Summarized History** | Per patient (weekly) | Summary generated on demand | Regenerated weekly | Doctor Summary Agent output |
| **Cross-Session Memory** | Per patient | `emergency_alerts`, `adherence_logs` | Persistent | Queried by agents when needed |
| **User Preferences** | Per user | `users` table preferences column | Persistent | Loaded at session start |

### 5.2 Conversation Window Strategy

```
                    ┌─────────────────────────────────────┐
                    │           Full History               │
                    │  (loaded from chat_history table)    │
                    └─────────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │         Summarized Context           │
                    │  (LLM-generated summary of older     │
                    │   messages beyond window)            │
                    └─────────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │         Active Window                │
                    │  (last 20 messages — included        │
                    │   verbatim in context)               │
                    └─────────────────────────────────────┘
                                      │
                                      ▼
                                  LLM Call
```

- Messages 1-50: Summarized into a single paragraph
- Messages 51-70: Included verbatim as chat_history
- This prevents context window overflow while preserving important context

### 5.3 Context Loaders

Each agent has a `build_context()` function that queries the database and populates
the initial state before the graph runs:

```python
async def build_chat_context(patient_id: str, db: AsyncSession) -> ChatAgentState:
    """Load patient data, chat history, medicines into initial state."""
    patient = await patient_repo.get_by_id(db, patient_id)
    medicines = await medicine_repo.get_active_by_patient(db, patient_id)
    history = await chat_repo.get_recent(db, patient_id, limit=20)
    return ChatAgentState(
        patient_id=patient_id,
        patient_context=summarize_patient(patient, medicines),
        chat_history=format_history(history),
        ...
    )
```

---

## 6. Checkpointing & Persistence

### 6.1 Checkpoint Strategy

LangGraph checkpoints are used for **resilience** and **observability**, not
for long-running persistence.

| Property | Design Decision |
|----------|----------------|
| **Provider** | `PostgresSaver` (production), `MemorySaver` (dev/test) |
| **When to checkpoint** | After every node execution |
| **What is stored** | Complete state dict (JSON-serialized) |
| **Retention** | 24 hours (TTL cleanup via background task) |
| **Why** | Resume on crash, debug failed executions, audit trail |

### 6.2 Checkpoint Schema

```sql
CREATE TABLE langgraph_checkpoints (
    checkpoint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL,              -- Unique per agent execution
    node_name VARCHAR(255) NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    parent_checkpoint_id UUID REFERENCES langgraph_checkpoints(checkpoint_id)
);

CREATE INDEX idx_checkpoints_thread ON langgraph_checkpoints(thread_id, created_at DESC);
CREATE INDEX idx_checkpoints_created ON langgraph_checkpoints(created_at);

-- TTL cleanup (run every hour)
DELETE FROM langgraph_checkpoints WHERE created_at < NOW() - INTERVAL '24 hours';
```

### 6.3 Thread ID Strategy

- `thread_id` = `{agent_name}:{request_id}`
- Example: `chat_agent:req_abc123`
- This scopes checkpoints to a single request execution
- For long-running operations (summary generation), the same thread_id can be
  reused to resume from the last checkpoint

### 6.4 When NOT to Checkpoint

- Checkpoints are **not used** for routine conversation history — that's stored in `chat_history`
- Checkpoints are **not used** as a primary data store — they are operational logs
- Checkpoints are **not preserved** across application restarts in dev (MemorySaver)

---

## 7. Error Recovery

### 7.1 Error Taxonomy

| Error Category | Examples | Recovery Strategy |
|----------------|----------|-------------------|
| **Transient** | LLM timeout, DB connection pool exhaustion, network glitch | Retry with exponential backoff |
| **LLM Quality** | JSON parse failure, incomplete response, hallucinated fields | Retry with stricter prompt, then fallback model |
| **Data Missing** | Patient not found, no medicines, empty report text | Return user-friendly error, skip dependent nodes |
| **Validation** | Invalid input, schema violation, guardrail block | Return error to user with explanation |
| **Permanent** | Invalid API key, corrupted state, out-of-token credit | Stop execution, log alert, return 500 |
| **Safety** | Guardrail violation (BLOCK), harmful content detected | Return safe default response, log audit event |

### 7.2 Node-Level Error Handler

Every LLM call node wraps execution in an error handler:

```python
async def safe_llm_call(
    state: AgentState,
    prompt_path: str,
    llm_client: LLMClient,
    input_vars: dict,
    max_retries: int = 2,
) -> tuple[dict | None, str | None]:
    """Execute an LLM call with error handling.

    Returns (parsed_output, error_message).
    On error, error_message is set and parsed_output is None.
    """
    for attempt in range(max_retries + 1):
        try:
            prompt = PromptLoader.load(prompt_path)
            rendered = prompt.render(**input_vars)
            response = await llm_client.complete(
                messages=[{"role": "user", "content": rendered}],
                response_format={"type": "json_object"},
            )
            parsed = json.loads(response)
            return parsed, None
        except json.JSONDecodeError as e:
            if attempt == max_retries:
                return None, f"Failed to parse LLM response after {max_retries} retries: {e}"
            continue
        except LLMTimeoutError as e:
            if attempt == max_retries:
                return None, f"LLM timed out after {max_retries} retries"
            await asyncio.sleep(2 ** attempt)  # exponential backoff
            continue
        except LLMAuthError:
            return None, "LLM authentication failed — check API key"
```

### 7.3 State-Level Error Accumulation

Errors are accumulated in the state's `errors` list, not raised as exceptions:

```python
# In a node:
result, error = await safe_llm_call(state, ...)
if error:
    state["errors"] = state.get("errors", []) + [
        {
            "node": "medical_extract_entities",
            "message": error,
            "timestamp": datetime.utcnow().isoformat(),
            "retry_count": state.get("retry_count", 0),
        }
    ]
    state["validation_status"] = "failed"
    return state  # Router checks errors and decides next step
```

### 7.4 Error Router

A global error router checks if accumulated errors exceed thresholds:

```python
def route_on_error(state: AgentState) -> str:
    """Check if errors require halting or can continue."""
    errors = state.get("errors", [])
    if not errors:
        return "continue_normal"

    fatal_errors = [e for e in errors if e.get("severity") == "fatal"]
    if fatal_errors:
        return "end_with_error"

    if len(errors) > 3:
        return "end_with_error"  # too many non-fatal errors

    return "continue_degraded"  # continue with reduced functionality
```

---

## 8. Retry Strategy

### 8.1 Retry Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Max retries (LLM calls) | 2 | 3 total attempts per node |
| Max retries (DB queries) | 1 | 2 total attempts (fast operations) |
| Backoff type | Exponential | `2^attempt` seconds |
| Max backoff | 30 seconds | Prevents excessive wait |
| Jitter | ±20% | Prevents thundering herd |
| Retryable errors | Timeout, 429, 503, ConnectionError, DB pool timeout | |
| Non-retryable errors | 401, 403, 400, InvalidInput, SchemaViolation | |

### 8.2 Retry Decorator

```python
def with_retry(
    max_retries: int = 2,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = (LLMTimeoutError, LLMRateLimitError, DBConnectionError),
):
    """Decorator for node functions that need retry logic."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(state, context, *args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(state, context, *args, **kwargs)
                except retryable_exceptions as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        delay += delay * 0.2 * (random.random() * 2 - 1)  # ±20% jitter
                        await asyncio.sleep(delay)
                        state["retry_count"] = attempt + 1
                    continue
            # All retries exhausted
            state["errors"] = state.get("errors", []) + [{
                "node": func.__name__,
                "message": str(last_error),
                "timestamp": datetime.utcnow().isoformat(),
                "retries_exhausted": True,
            }]
            return state
        return wrapper
    return decorator
```

### 8.3 Retry Budget

Each request has a **retry budget** of 15 seconds total. If retries consume more
than 15 seconds combined, the request degrades rather than retrying further:

```python
RETRY_BUDGET_SECONDS = 15

async def within_retry_budget(start_time: datetime) -> bool:
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    return elapsed < RETRY_BUDGET_SECONDS
```

---

## 9. Fallback LLM

### 9.1 Model Hierarchy

```
                    gpt-4o (Primary — Best Quality)
                        │
                        ▼
              gpt-4o-mini (Fallback 1 — Fast & Cheap)
                        │
                        ▼
    gpt-3.5-turbo (Fallback 2 — Emergency fallback)
                        │
                        ▼
           Rule-based response (Final fallback — No LLM)
```

### 9.2 Fallback Triggers

| Condition | Action |
|-----------|--------|
| Primary model returns 429 (rate limited) | Immediately fall back, don't retry primary |
| Primary model times out (>15s) | Fall back to mini for this call |
| Primary model returns malformed JSON twice | Fall back to mini, log error |
| All API models fail | Return rule-based safe response |
| API key invalid | Return rule-based, raise alert |
| Budget exhausted | Fall back to mini automatically |

### 9.3 Model Selection Per Agent

| Agent | Primary | Fallback 1 | Fallback 2 |
|-------|---------|------------|------------|
| Medical Report | gpt-4o-mini | gpt-3.5-turbo | Rule-based regex |
| Patient Chat | gpt-4o | gpt-4o-mini | gpt-3.5-turbo |
| Emergency | gpt-4o | gpt-4o-mini | Rule-based (always HIGH) |
| Doctor Summary | gpt-4o | gpt-4o-mini | Structured template |
| Reminder (message only) | gpt-4o-mini | gpt-3.5-turbo | Template-based |

### 9.4 Fallback Router Implementation

```python
class LLMClient:
    """Unified LLM client with automatic fallback."""

    MODEL_PRIORITY = {
        "medical": ["gpt-4o-mini", "gpt-3.5-turbo", "rule"],
        "chat": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "rule"],
        "emergency": ["gpt-4o", "gpt-4o-mini", "rule"],
        "summary": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "reminder": ["gpt-4o-mini", "gpt-3.5-turbo", "rule"],
    }

    async def complete(
        self,
        prompt: str,
        agent_type: str,
        response_format: dict | None = None,
    ) -> str:
        models = self.MODEL_PRIORITY.get(agent_type, ["gpt-4o-mini", "rule"])
        for model in models:
            if model == "rule":
                return self._rule_based_fallback(prompt, agent_type)
            try:
                return await self._try_model(model, prompt, response_format)
            except (LLMError, RateLimitError) as e:
                logger.warning(f"Model {model} failed: {e}. Trying next.")
                continue
        return self._rule_based_fallback(prompt, agent_type)

    def _rule_based_fallback(self, prompt: str, agent_type: str) -> str:
        """Return a safe default when all LLMs fail."""
        defaults = {
            "medical": '{"disease": "", "medicines": [], "follow_up_date": null}',
            "chat": "I'm sorry, I'm having trouble connecting to my AI service. "
                    "Please try again in a few moments.",
            "emergency": '{"risk_level": "HIGH", "analysis": "Unable to analyze. '
                         'Defaulting to HIGH for safety.", "recommendations": []}',
            "summary": "Summary generation is temporarily unavailable.",
            "reminder": "This is a reminder to take your medication.",
        }
        return defaults.get(agent_type, "Service temporarily unavailable.")
```

---

## 10. Tool Calling

### 10.1 Tool Philosophy

Tools are used **sparingly** and **only for data access actions** that the LLM
cannot do through the prompt. The primary AI pattern is **structured output**,
not tool calling.

### 10.2 Approved Tools

| Tool Name | Agent | Description | Arguments | Returns |
|-----------|-------|-------------|-----------|---------|
| `get_patient_info` | Chat, Summary | Fetch patient demographics | `patient_id: str` | Patient dict |
| `get_active_medicines` | Chat, Summary | List active medicines | `patient_id: str` | Medicine list |
| `get_recent_reports` | Chat, Summary | List recent reports | `patient_id: str, limit: int` | Report list |
| `get_adherence_stats` | Chat, Summary | Get adherence data | `patient_id: str, days: int` | Stats dict |
| `get_chat_history` | Chat | Get recent conversation | `patient_id: str, limit: int` | Message list |
| `get_appointments` | Chat | Get upcoming appointments | `patient_id: str` | Appointment list |
| `get_emergency_alerts` | Summary, Emergency | Get recent alerts | `patient_id: str, days: int` | Alert list |
| `search_reports_vector` | Chat | Query ChromaDB for context | `query: str, patient_id: str` | Chunk list |

### 10.3 Tool Definition Format

```python
from typing import Any

# Tools are defined as JSON schema for OpenAI function calling
CREATE_ALERT_TOOL = {
    "type": "function",
    "function": {
        "name": "create_emergency_alert",
        "description": "Create an emergency alert record for a patient.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "Patient UUID"},
                "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                "analysis": {"type": "string"},
                "recommendations": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["patient_id", "risk_level", "analysis"],
        },
    },
}
```

### 10.4 Tool Execution

```python
class ToolExecutor:
    """Executes tool calls requested by the LLM."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.registry = {
            "get_patient_info": self._get_patient_info,
            "get_active_medicines": self._get_active_medicines,
            "get_recent_reports": self._get_recent_reports,
            "get_adherence_stats": self._get_adherence_stats,
            "get_chat_history": self._get_chat_history,
            "get_appointments": self._get_appointments,
            "get_emergency_alerts": self._get_emergency_alerts,
            "search_reports_vector": self._search_reports_vector,
        }

    async def execute(self, tool_name: str, arguments: dict) -> Any:
        handler = self.registry.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")
        return await handler(**arguments)
```

### 10.5 When NOT to Use Tools

- ✗ Do NOT create tools that modify data (use dedicated API endpoints)
- ✗ Do NOT create tools that send notifications (use background tasks)
- ✗ Do NOT create tools that access other patients' data (use patient_id scoping)
- ✗ Do NOT create tools that run LLM calls (that's what agents are for)

---

## 11. Structured Outputs & JSON Schemas

### 11.1 Strategy

All LLM calls return **structured JSON** using OpenAI's `response_format` parameter
when available. When not available, JSON is extracted from the response text and
validated against the schema.

### 11.2 Schema Registry

Each prompt has a corresponding JSON schema in `backend/prompts/schemas/`:

```
backend/prompts/
├── medical/
│   ├── report_analysis.md
│   └── schemas/
│       └── report_analysis.json
├── chat/
│   ├── patient_chat.md
│   └── schemas/
│       └── patient_chat.json
...
```

### 11.3 Schema Validation Pipeline

```python
class SchemaValidator:
    """Validates LLM output against expected JSON schema."""

    def __init__(self):
        self.validators: dict[str, jsonschema.Draft7Validator] = {}

    def validate(self, prompt_path: str, data: dict) -> ValidationResult:
        """Validate data against the schema for the given prompt."""
        schema = self._load_schema(prompt_path)
        errors = []
        for error in jsonschema.Draft7Validator(schema).iter_errors(data):
            errors.append({
                "path": list(error.absolute_path),
                "message": error.message,
                "validator": error.validator,
            })
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            data=data,
        )

    def repair(self, prompt_path: str, data: dict) -> dict:
        """Attempt to repair common schema violations."""
        schema = self._load_schema(prompt_path)
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                data[field] = self._default_for_type(schema["properties"][field])
        return data
```

### 11.4 Per-Agent Output Schemas

**medical/report_analysis** — Extract clinical data:
```json
{
  "type": "object",
  "required": ["disease", "medicines", "follow_up_date", "notes"],
  "properties": {
    "disease": {"type": "string"},
    "medicines": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "dosage", "frequency"],
        "properties": {
          "name": {"type": "string"},
          "dosage": {"type": "string"},
          "frequency": {"type": "string"},
          "duration": {"type": ["string", "null"]},
          "route": {"type": "string", "enum": ["oral", "topical", "IV", "IM", "subcutaneous", "inhalation", "other"]},
          "instructions": {"type": "string"}
        }
      }
    },
    "follow_up_date": {"type": ["string", "null"], "format": "date"},
    "doctor_instructions": {"type": "string"},
    "notes": {"type": "string"}
  }
}
```

**chat/patient_chat** — Generate response:
```json
{
  "type": "object",
  "required": ["response", "sources", "requires_escalation"],
  "properties": {
    "response": {"type": "string", "maxLength": 2000},
    "sources": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": {"type": "string", "enum": ["report", "medicine", "appointment", "general"]},
          "reference": {"type": "string"}
        }
      }
    },
    "requires_escalation": {"type": "boolean"},
    "follow_up_question": {"type": ["string", "null"]}
  }
}
```

**emergency/symptom_triage** — Classify urgency:
```json
{
  "type": "object",
  "required": ["risk_level", "analysis", "recommendations", "disclaimer"],
  "properties": {
    "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
    "analysis": {"type": "string", "maxLength": 1000},
    "recommendations": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4},
    "disclaimer": {"type": "string"},
    "key_symptoms_identified": {"type": "array", "items": {"type": "string"}}
  }
}
```

**summary/doctor_summary** — Clinical summary:
```json
{
  "type": "object",
  "required": ["summary", "adherence_metrics", "risk_flags"],
  "properties": {
    "summary": {
      "type": "object",
      "properties": {
        "patient_overview": {"type": "string"},
        "medication_adherence": {"type": "string"},
        "reported_concerns": {"type": "string"},
        "ai_interactions": {"type": "string"},
        "recommendations": {"type": "string"}
      }
    },
    "adherence_metrics": {
      "type": "object",
      "properties": {
        "overall_rate": {"type": "number", "minimum": 0, "maximum": 100},
        "missed_doses": {"type": "integer", "minimum": 0},
        "improving": {"type": "boolean"}
      }
    },
    "risk_flags": {"type": "array", "items": {"type": "string"}},
    "next_review_date": {"type": ["string", "null"]}
  }
}
```

### 11.5 Repair Strategies

| Violation | Repair |
|-----------|--------|
| Missing required field | Fill with null or empty array |
| Wrong type (string instead of array) | Attempt JSON parse; if fails, wrap in array |
| Enum violation | Replace with closest valid value or default |
| MaxLength exceeded | Truncate to maxLength |
| Wrong format (date, email) | Leave as-is, log warning, downstream validates |
| Extra unknown fields | Preserve them (forward-compatible) |

---

## 12. Hallucination Prevention

### 12.1 Defense Layers

```
                    ┌─────────────────────────────┐
                    │   Layer 1: Prompt Design     │
                    │   - Explicit constraints     │
                    │   - "Only use provided data" │
                    │   - Output schema enforced   │
                    └─────────────────────────────┘
                                   │
                    ┌─────────────────────────────┐
                    │   Layer 2: Context Scoping   │
                    │   - RAG retrieval scoped to  │
                    │     patient_id               │
                    │   - No external knowledge     │
                    └─────────────────────────────┘
                                   │
                    ┌─────────────────────────────┐
                    │   Layer 3: Output Validation │
                    │   - JSON schema validation   │
                    │   - Enum constraint checks   │
                    │   - Required field presence  │
                    └─────────────────────────────┘
                                   │
                    ┌─────────────────────────────┐
                    │   Layer 4: Factual Checks    │
                    │   - Cross-reference with     │
                    │     source documents         │
                    │   - Consistency verification │
                    └─────────────────────────────┘
                                   │
                    ┌─────────────────────────────┐
                    │   Layer 5: Safety Guardrails │
                    │   - Medical diagnosis block  │
                    │   - Dosage change block      │
                    │   - Escalation advisory      │
                    └─────────────────────────────┘
```

### 12.2 Layer Details

**Layer 1 — Prompt Design:**
- Every prompt includes "Only use information from the provided context"
- Input variables explicitly named to scope the LLM's attention
- Few-shot examples in every prompt demonstrate expected behavior
- System-level: "You are a healthcare assistant — never diagnose"

**Layer 2 — Context Scoping:**
- Chat Agent: RAG retrieval is filtered by `patient_id` at the database level
- Summary Agent: All data is pre-fetched from DB before LLM call — no tool calling for data
- Medical Agent: Extraction is constrained to text provided — no external medical knowledge
- Emergency Agent: Classification rules are in the prompt — no diagnostic language allowed

**Layer 3 — Output Validation:**
- JSON schema validated after every LLM call
- Enums restricted to allowed values (e.g., `risk_level` must be LOW/MEDIUM/HIGH)
- Numeric ranges enforced (adherence_rate 0-100)
- String length limits prevent rambling

**Layer 4 — Factual Cross-Reference:**
- `diagnosis_check` prompt specifically verifies extracted disease against source text
- Doctor Summary metrics (adherence_rate) are computed from DB data, not from LLM
- Chat responses require source citations — uncited statements are flagged
- If confidence is below threshold, mark for human review

**Layer 5 — Safety Guardrails:**
- `system/guardrails.md` evaluated on every response before delivery
- BLOCK-level violations (diagnosis, dosage changes) stop the response
- WARN-level violations (overconfidence, jargon) logged but allowed
- Escalation check: if ANY symptom sounds serious, flag for Emergency Agent

### 12.3 Specific Anti-Hallucination Rules

| Rule | Applied To | Implementation |
|------|-----------|---------------|
| No invented medicines | Chat Agent | Validate medicine names against DB list before responding |
| No invented patient data | All agents | All data pre-loaded into state before LLM call |
| No numerical claims | Chat Agent | All numbers (dosage, dates) must reference specific source |
| No prognostic statements | All agents | Prompt-level prohibition ("You cannot predict outcomes") |
| Source citation required | Chat Agent | Every claim must include `source` field in response JSON |
| Confidence threshold | Medical Agent | Extraction < 0.7 confidence → human review flag |
| Consistency check | Medical Agent | `diagnosis_check` must pass before storing results |

### 12.4 Hallucination Detection Metrics

After each LLM call, the system computes a **hallucination risk score**:

```python
def compute_hallucination_risk(
    response: dict,
    context: str,
    schema: dict,
) -> float:
    """Compute hallucination risk score 0.0 (safe) to 1.0 (likely hallucinated)."""
    risk = 0.0
    required = schema.get("required", [])

    # Missing required fields increase risk
    missing = [f for f in required if f not in response]
    risk += len(missing) * 0.1

    # Fields with unexpected values
    if "risk_level" in response and response["risk_level"] not in ("LOW", "MEDIUM", "HIGH"):
        risk += 0.3

    # Response length anomaly (too short or too long vs expected)
    expected_length = 500  # Configurable per prompt
    actual_length = len(json.dumps(response))
    if actual_length < expected_length * 0.1:
        risk += 0.2

    return min(risk, 1.0)
```

---

## 13. Medical Safety

### 13.1 Safety Architecture

```
Patient Input
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│                   INPUT SAFETY LAYER                      │
│  • Input validation (Pydantic schema)                    │
│  • Content moderation (harmful input detection)           │
│  • Rate limiting (per-patient, per-endpoint)              │
│  • Authentication + authorization (role check)            │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│                   AI PROCESSING LAYER                     │
│  • Prompt-level safety constraints                       │
│  • Patient-scoped context (no cross-patient data)         │
│  • Structured output (no free-form generation)            │
│  • No diagnostic language allowed at prompt level         │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│                   OUTPUT SAFETY LAYER                     │
│  • Guardrail prompt evaluation                           │
│  • JSON schema validation                                │
│  • Medical disclaimer injection                          │
│  • Escalation check (automatically flag HIGH risk)        │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│                   AUDIT LAYER                             │
│  • Full interaction logging                              │
│  • Guardrail violation audit trail                        │
│  • Human review queue for flagged responses               │
│  • Weekly safety review reports                          │
└──────────────────────────────────────────────────────────┘
```

### 13.2 Forbidden Outputs (Non-Negotiable)

The following outputs are **strictly forbidden** and BLOCKED by the guardrail layer:

1. **Diagnoses**: "You have [disease]" — use "Your symptoms are consistent with..."
2. **Dosage changes**: "Take an extra pill" — use "Please consult your doctor about dosage"
3. **Treatment recommendations**: "You should take [medicine]" — use "Your doctor prescribed..."
4. **Prognosis**: "You will recover in X days" — use "Recovery times vary, consult your doctor"
5. **Emergency discouragement**: "You don't need to go to the ER" — NEVER
6. **Cross-patient data**: Any reference to other patients' information
7. **Overconfidence**: "I am certain that..." — use "Based on your records..."

### 13.3 Medical Disclaimer Protocol

Every AI-generated response that provides health information must include:

- **Chat responses**: Appended automatically if health information is conveyed
- **Emergency responses**: Included in the recommendations array (required field)
- **Summary outputs**: Not needed (doctor-facing, assumes clinical training)

```python
DISCLAIMERS = {
    "chat": "I'm an AI assistant, not a doctor. Always consult your healthcare provider "
            "for medical advice. If you're experiencing a medical emergency, call 911.",
    "emergency_low": "This is an automated assessment and does not constitute a "
                     "medical diagnosis. Consult your doctor if symptoms persist.",
    "emergency_high": "This is an automated alert. Please seek immediate medical attention. "
                      "Do not wait for a doctor to contact you.",
}
```

### 13.4 Escalation Rules

| Condition | Action |
|-----------|--------|
| Patient mentions chest pain, difficulty breathing, severe bleeding | Automatically escalate to Emergency Agent |
| Patient expresses suicidal ideation or self-harm | BLOCK response → Emergency Agent → Doctor notification |
| Guardrail produces BLOCK violation | Log to audit table, send to human review queue |
| LLM confidence < 0.5 on extraction | Flag for human review, store with `requires_human_review=True` |
| 3+ LOW alerts in 24 hours | Auto-escalate to MEDIUM review by doctor |

### 13.5 Human-in-the-Loop

For high-stakes decisions, the system **never** acts autonomously:

- **Emergency alerts with HIGH risk**: Doctor must acknowledge before patient is notified (except 911 recommendation)
- **Extracted medicines with < 0.7 confidence**: Stored as "pending_review" — not active until doctor approves
- **Summary generation**: Doctor-facing only — no automated actions based on summaries
- **Medication changes**: Only doctors can make them — AI never suggests or implements

### 13.6 Audit Trail

All AI interactions are logged in a dedicated audit table:

```sql
CREATE TABLE ai_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    node_name VARCHAR(100),
    patient_id UUID,
    prompt_path VARCHAR(255),
    prompt_content TEXT,                  -- The rendered prompt sent to LLM
    llm_response JSONB,                  -- Raw LLM response
    validated_output JSONB,              -- After schema validation
    guardrail_result JSONB,              -- Guardrail evaluation
    hallucination_risk FLOAT,            -- 0.0 to 1.0
    latency_ms INTEGER,                  -- Time taken for this interaction
    model_used VARCHAR(50),              -- Which model served this request
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 14. Cost Optimization

### 14.1 Model Selection by Task

| Task | Model | Input Tokens (avg) | Output Tokens (avg) | Cost per 1K calls | Annual Cost (est) |
|------|-------|-------------------|--------------------|-------------------|-------------------|
| Report extraction | gpt-4o-mini | 2,000 | 500 | $0.08 | $29 |
| Chat response | gpt-4o | 3,500 | 300 | $2.10 | $767 |
| Emergency triage | gpt-4o | 1,000 | 400 | $0.70 | $26 |
| Doctor summary | gpt-4o | 5,000 | 800 | $2.90 | $106 |
| Adherence message | gpt-4o-mini | 500 | 100 | $0.02 | $7 |
| Guardrail check | gpt-4o-mini | 2,000 | 200 | $0.06 | $22 |

**Estimated total annual cost: ~$957** for 100K chat conversations + 10K reports + 5K summaries + 5K emergencies.

### 14.2 Cost Saving Strategies

| Strategy | Savings | Implementation |
|----------|---------|---------------|
| **Prompt compression** | ~20% | Remove unnecessary whitespace, compress few-shot examples |
| **Context window management** | ~30% | Only include relevant context, not full history |
| **Caching identical prompts** | ~5% | Cache rendered prompts for common patterns |
| **Batch processing** | ~15% | Batch non-urgent summaries into off-peak hours |
| **Model tiering by task** | ~40% | Use gpt-4o-mini for extraction, gpt-4o only for chat/emergency |
| **Early exit on guardrails** | ~2% | If input fails guardrails, skip expensive LLM calls |

### 14.3 Cost Tracking

```python
class CostTracker:
    """Track per-request LLM costs."""

    MODEL_COSTS = {
        "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
        "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
        "gpt-3.5-turbo": {"input": 0.50 / 1_000_000, "output": 1.50 / 1_000_000},
    }

    def track(self, model: str, input_tokens: int, output_tokens: int) -> float:
        costs = self.MODEL_COSTS.get(model, self.MODEL_COSTS["gpt-4o-mini"])
        return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1000
```

### 14.4 Budget Alerts

- **Daily budget**: Configurable via `settings.LLM_DAILY_BUDGET` (default $50)
- **Alert at 80%**: Log warning, switch non-critical agents to fallback model
- **Alert at 100%**: Block non-essential LLM calls (adherence messages, follow-up questions)
- **Emergency budget**: $50/day reserve for safety-critical calls (emergency triage)

---

## 15. Latency Optimization

### 15.1 Target Latencies

| Operation | Target p50 | Target p95 | Deadline |
|-----------|-----------|-----------|----------|
| Chat response | 2s | 5s | 10s |
| Report extraction | 3s | 8s | 15s |
| Emergency triage | 3s | 6s | 10s |
| Doctor summary | 5s | 12s | 20s |
| Guardrail check | 1s | 3s | 5s |

### 15.2 Optimization Techniques

| Technique | Impact | Where Applied |
|-----------|--------|---------------|
| **Streaming responses** | Perceived 2x faster | Chat Agent response |
| **Parallel DB queries** | 40-60% faster data loading | Summary Agent (load 5 tables in parallel) |
| **Context pre-loading** | 30% faster first token | Chat Agent (pre-fetch on request receive) |
| **Prompt caching** | 20% faster (no re-encoding) | System prompts, frequent patterns |
| **Smaller model for sub-tasks** | 3x faster | Medical extraction with mini vs 4o |
| **Early validation** | Avoid wasted LLM calls | Validate input before invoking LLM |
| **Timeout management** | Prevent long tail | 15s per LLM call, fall back after timeout |

### 15.3 Parallel Execution Design

Nodes that are I/O-bound and independent run in parallel:

```python
# Orchestrator parallel dispatch
async def run_parallel(state: SummaryAgentState) -> SummaryAgentState:
    """Load all patient data in parallel."""
    async with asyncio.TaskGroup() as tg:
        patient_task = tg.create_task(patient_repo.get_by_id(db, state["patient_id"]))
        medicines_task = tg.create_task(medicine_repo.get_active(db, state["patient_id"]))
        alerts_task = tg.create_task(alert_repo.get_recent(db, state["patient_id"]))
        chat_task = tg.create_task(chat_repo.get_summary(db, state["patient_id"]))

    state["patient_data"] = patient_task.result()
    state["medicines"] = medicines_task.result()
    state["alerts"] = alerts_task.result()
    state["chat_summary"] = chat_task.result()
    return state
```

### 15.4 Timeout Configuration

```python
# Per-LLM-call timeout (applied at HTTP client level)
LLM_TIMEOUT = {
    "gpt-4o": 15.0,       # Seconds — slower model gets more time
    "gpt-4o-mini": 10.0,  # Seconds — faster model
    "gpt-3.5-turbo": 8.0, # Seconds — fastest
}

# Per-node timeout (total including retries)
NODE_TIMEOUT = {
    "gpt-4o": 30.0,       # 15s * 2 retries max
    "gpt-4o-mini": 20.0,
}

# Total request timeout
REQUEST_TIMEOUT = 60.0    # Any single request exceeding this is terminated
```

---

## 16. Streaming Strategy

### 16.1 When to Stream

| Scenario | Stream? | Reason |
|----------|---------|--------|
| Patient chat response | **Yes** | Perceived latency improvement, better UX |
| Report extraction | No | Returns JSON, streaming doesn't help |
| Emergency triage | **Yes** | First token (risk level) is most critical |
| Doctor summary | No | Background generation, doctor reads later |
| Guardrail check | No | Must evaluate full response before delivery |
| Adherence message | No | Short, pre-generated messages |

### 16.2 Chat Streaming Architecture

```
Client                    Server                    LLM
  │                         │                       │
  │── POST /chat/message ──>│                       │
  │                         │── Pre-fetch context ──>│
  │                         │<── context ready ─────│
  │                         │                       │
  │                         │── Start LLM stream ──>│
  │<── SSE: token 1 ───────│<── token 1 ───────────│
  │<── SSE: token 2 ───────│<── token 2 ───────────│
  │<── SSE: token 3 ───────│<── token 3 ───────────│
  │                         │                       │
  │                         │── Guardrail check ───>│
  │                         │<── safe to deliver ───│
  │<── SSE: [DONE] ───────│                       │
  │                         │── Store in DB ────────│
  │                         │                       │
```

### 16.3 SSE Protocol

```python
# Server-Sent Events format for chat streaming
async def stream_chat_response(question: str, patient_id: str):
    """Stream tokens via SSE to the client."""
    async with fastapi.responses.StreamingResponse(
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    ) as response:
        # Step 1: Send context start
        await response.write(f"event: context_start\ndata: {json.dumps({'source': 'patient_records'})}\n\n")

        # Step 2: Stream tokens
        async for token in llm_client.stream(prompt, model="gpt-4o"):
            await response.write(f"event: token\ndata: {json.dumps({'token': token})}\n\n")

        # Step 3: Send sources
        await response.write(f"event: sources\ndata: {json.dumps({'sources': sources})}\n\n")

        # Step 4: Done
        await response.write("event: done\ndata: {}\n\n")
```

### 16.4 Streaming Edge Cases

| Case | Handling |
|------|----------|
| Client disconnects mid-stream | Detect via `asyncio.CancelledError`, abort LLM call |
| LLM error mid-stream | Send `event: error`, close stream gracefully |
| Guardrail violation mid-stream | Not possible — guardrails run on complete response |
| Slow client | Buffer up to 50 tokens, flush on buffer full or 200ms elapsed |
| Rate limit during stream | Complete current stream, reject next request |

---

## 17. Prompt Versioning

### 17.1 Version Scheme

Prompts use **semantic versioning**: `MAJOR.MINOR.PATCH`

| Bump | When | Example |
|------|------|---------|
| **MAJOR** | Breaking change to output schema or behavior | Adding new required field, changing enum values |
| **MINOR** | Non-breaking addition or improvement | Adding new example, clarifying instruction |
| **PATCH** | Minor fix, typo, formatting | Grammar fix, whitespace cleanup |

### 17.2 Version Manifest

A `backend/prompts/VERSIONS.json` file tracks every prompt version:

```json
{
  "schema_version": "1.0",
  "prompts": {
    "medical/report_analysis": {
      "current_version": "1.2.0",
      "history": [
        {"version": "1.0.0", "date": "2026-07-14", "author": "AI Healthcare Team", "change": "Initial creation"},
        {"version": "1.1.0", "date": "2026-07-21", "author": "Dr. Smith", "change": "Added route enum validation"},
        {"version": "1.2.0", "date": "2026-08-01", "author": "AI Healthcare Team", "change": "Added confidence scoring instruction"}
      ],
      "checksum": "sha256:a1b2c3d4..."
    }
  }
}
```

### 17.3 Checksum Verification

Every prompt file has a SHA-256 checksum that is verified before loading:

```python
class PromptLoader:
    @classmethod
    def load(cls, path: str) -> Prompt:
        file_path = PROMPTS_DIR / f"{path}.md"
        content = file_path.read_text(encoding="utf-8")

        # Verify checksum against manifest
        expected_hash = cls._get_expected_checksum(path)
        actual_hash = hashlib.sha256(content.encode()).hexdigest()
        if expected_hash and actual_hash != expected_hash:
            logger.warning(f"Prompt {path} checksum mismatch — file may have been modified")

        return cls._parse(content)
```

### 17.4 Rollback Process

```python
class PromptRollback:
    """Roll back a prompt to a previous version."""

    @classmethod
    async def rollback(cls, prompt_path: str, target_version: str) -> Prompt:
        """Restore a prompt file to a previous version from git."""
        import subprocess
        result = subprocess.run(
            ["git", "show", f"HEAD:backend/prompts/{prompt_path}.md"],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        # Parse version from frontmatter
        # If version matches target, restore file
        # If not, walk git log until version is found
```

### 17.5 Prompt Review Workflow

```
Prompt Change Proposed
    │
    ▼
┌─────────────────────┐
│  Change Description  │  What changed and why
│  Schema Impact       │  Does the output schema change?
│  Safety Impact       │  Any new safety considerations?
│  Performance Impact  │  Token count change?
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Review (2 approvals) │
│  • Technical review   │  AI engineer
│  • Clinical review    │  Medical professional (for medical prompts)
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  A/B Test            │  10% of traffic, compare metrics
│  • Response quality  │
│  • Hallucination rate│
│  • Safety violations │
│  • Token count       │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Gradual Rollout     │  25% → 50% → 100%
│  • Monitor metrics   │
│  • Rollback ready    │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Version Published   │
│  VERSIONS.json updated│
│  Old version archived │
└─────────────────────┘
```

### 17.6 Prompt Testing

Each prompt has associated test cases in `backend/tests/prompts/`:

```
backend/tests/prompts/
├── test_prompt_render.py       # Verify all prompts render without error
├── test_prompt_schemas.py      # Verify all output schemas are valid JSON Schema
├── test_medical_prompts.py     # Medical-specific test cases
├── test_chat_prompts.py        # Chat-specific test cases
├── test_emergency_prompts.py   # Emergency-specific test cases
├── test_summary_prompts.py     # Summary-specific test cases
├── test_rag_prompts.py         # RAG-specific test cases
└── test_guardrails.py          # Guardrail evaluation tests
└── fixtures/                   # Example inputs/outputs for each prompt
    ├── medical_report_input.txt
    ├── medical_report_output.json
    ├── chat_input.txt
    ├── chat_output.json
    ...
```

---

## 18. Evaluation Strategy

### 18.1 Evaluation Dimensions

| Dimension | Metric | Target | Measurement Method |
|-----------|--------|--------|-------------------|
| **Quality** | Response accuracy | >95% | Human evaluation on test set |
| **Safety** | Guardrail violation rate | <0.1% | Automated guardrail checks |
| **Hallucination** | Unsupported claim rate | <1% | Human review of sampled responses |
| **Latency** | p95 response time | <5s chat, <8s extraction | Production monitoring |
| **Cost** | Cost per request | <$0.01 chat, <$0.001 extraction | CostTracker |
| **Availability** | LLM success rate | >99.5% | Health check + fallback metrics |

### 18.2 Evaluation Pipeline

```
                    ┌─────────────────────────────────────────────┐
                    │         Automated Evaluation Suite           │
                    │                                              │
                    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
                    │  │ Schema   │  │ Unit     │  │ Guardrail│  │
                    │  │ Tests    │  │ Tests    │  │ Tests    │  │
                    │  └──────────┘  └──────────┘  └──────────┘  │
                    │                                              │
                    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
                    │  │ Prompt   │  │ LLM      │  │ Cost     │  │
                    │  │ Tests    │  │ Fixtures │  │ Tests    │  │
                    │  └──────────┘  └──────────┘  └──────────┘  │
                    └─────────────────────────────────────────────┘
                                        │
                    ┌─────────────────────────────────────────────┐
                    │           LLM-as-Judge Evaluation            │
                    │                                              │
                    │  For every test case:                        │
                    │  1. Run prompt → get LLM output              │
                    │  2. gpt-4o evaluates output against criteria  │
                    │  3. Score 1-5 on: accuracy, safety, format   │
                    │  4. Flag scores < 3 for human review         │
                    └─────────────────────────────────────────────┘
                                        │
                    ┌─────────────────────────────────────────────┐
                    │            Human Evaluation                   │
                    │                                              │
                    │  Monthly sample of 500 responses:            │
                    │  • Medical accuracy review (doctor required) │
                    │  • Safety compliance review                  │
                    │  • Patient satisfaction proxy (chat)         │
                    │  • Clinical utility (summaries)              │
                    └─────────────────────────────────────────────┘
```

### 18.3 Evaluation Test Suites

**Suite 1 — Unit Tests (CI, every commit)**

```python
# Tests that run on every PR
class TestMedicalExtraction:
    async def test_valid_prescription_extracts_medicine(self):
        """Should extract medicine name, dosage, frequency."""
        result = await run_agent("medical", {"raw_text": "Metformin 500mg bid"})
        assert result["extracted_data"]["medicines"][0]["name"] == "Metformin"
        assert result["validation_status"] == "validated"

    async def test_empty_text_returns_error(self):
        """Should set error for empty input."""
        result = await run_agent("medical", {"raw_text": ""})
        assert result["error"] is not None

    async def test_output_matches_schema(self):
        """Should always return valid JSON matching report_analysis schema."""
        result = await run_agent("medical", {"raw_text": "Test"})
        schema = load_schema("medical/report_analysis")
        jsonschema.validate(result["extracted_data"], schema)
```

**Suite 2 — LLM Fixture Tests (CI, daily)**

```python
# Tests with pre-recorded LLM responses for deterministic testing
class TestChatGuardrails:
    async def test_blocks_diagnosis(self):
        """Should block response if LLM outputs diagnosis."""
        output = await run_with_fixture("chat", "fixtures/llm_diagnosis_response.json")
        assert output["guardrail_check"]["action"] == "block"

    async def test_allows_safe_response(self):
        """Should allow response if guardrails pass."""
        output = await run_with_fixture("chat", "fixtures/llm_safe_response.json")
        assert output["guardrail_check"]["action"] == "allow"
```

**Suite 3 — Real LLM Evaluation (nightly)**

```python
# Tests that call actual LLMs (costly, run nightly)
class TestEmergencyTriageNightly:
    @pytest.mark.nightly
    async def test_chest_pain_returns_high(self):
        result = await run_agent("emergency", {"symptoms": "Sharp chest pain"})
        assert result["risk_level"] == "HIGH"

    @pytest.mark.nightly
    async def test_mild_cold_returns_low(self):
        result = await run_agent("emergency", {"symptoms": "Runny nose, sneezing"})
        assert result["risk_level"] == "LOW"
```

### 18.4 LLM-as-Judge Evaluation

```python
class LLMJudge:
    """Use gpt-4o to evaluate outputs from other LLM calls."""

    EVALUATION_CRITERIA = {
        "medical_extraction": """
        Score the following medical extraction from 1-5:
        - 5: Perfect — all fields correct, no missing data
        - 4: Good — minor missing optional fields
        - 3: Acceptable — all required fields present, some inaccuracies
        - 2: Poor — missing required fields or significant inaccuracies
        - 1: Failed — completely wrong or unparseable

        Return JSON: {"score": int, "reasoning": str, "issues": [str]}
        """,
        "chat_response": """
        Score the following chat response from 1-5:
        - 5: Perfect — accurate, empathetic, well-sourced
        - 4: Good — accurate but minor tone or clarity issues
        - 3: Acceptable — accurate but could be more helpful
        - 2: Poor — inaccurate, unsafe, or missing sources
        - 1: Failed — violates safety rules or completely wrong

        Return JSON: {"score": int, "reasoning": str, "issues": [str]}
        """,
    }

    async def evaluate(self, prompt_type: str, input_data: dict, output: dict) -> dict:
        criteria = self.EVALUATION_CRITERIA.get(prompt_type)
        judge_prompt = f"{criteria}\n\nInput: {json.dumps(input_data)}\n\nOutput: {json.dumps(output)}"
        response = await self.judge_llm.complete(judge_prompt, response_format={"type": "json_object"})
        return json.loads(response)
```

### 18.5 A/B Testing Framework

```python
class PromptABTest:
    """Route traffic between prompt versions for evaluation."""

    def __init__(self, prompt_path: str):
        self.prompt_path = prompt_path
        self.variants = self._get_active_variants()

    def select_variant(self, request_id: str) -> str:
        """Deterministically select variant based on request_id."""
        hash_val = int(hashlib.md5(request_id.encode()).hexdigest(), 16)
        return "control" if hash_val % 100 >= 10 else "treatment"

    async def track(self, request_id: str, variant: str, metrics: dict):
        """Record metrics for this A/B test sample."""
        await ab_test_db.record({
            "request_id": request_id,
            "prompt_path": self.prompt_path,
            "variant": variant,
            "latency_ms": metrics["latency_ms"],
            "token_count": metrics["token_count"],
            "guardrail_violation": metrics.get("guardrail_violation", False),
            "hallucination_score": metrics.get("hallucination_score", 0.0),
        })
```

### 18.6 Continuous Monitoring

Production monitoring dashboards track:

| Dashboard | Metrics | Alert Threshold |
|-----------|---------|-----------------|
| **LLM Health** | Success rate, latency, token usage | <99% success rate |
| **Guardrail Violations** | Block rate, warn rate by agent | >1% block rate |
| **Cost** | Daily cost, cost per request | >$50/day |
| **Response Quality** | Hallucination risk score, schema validation failures | >5% failure rate |
| **Safety** | Medical safety violations | ANY violation = immediate alert |
| **Fallback Rate** | How often fallback models are used | >5% fallback rate |

### 18.7 Evaluation Cadence

| Frequency | Activity | Responsible |
|-----------|----------|-------------|
| Every commit | Unit tests + prompt render tests | CI pipeline |
| Daily | Nightly LLM evaluation + cost report | Automated |
| Weekly | Safety review of guardrail violations | AI engineer |
| Monthly | Human evaluation of 500 responses | AI engineer + medical reviewer |
| Per-release | Full A/B test of changed prompts | AI engineer |
| Per-incident | Root cause analysis of safety event | AI engineer + medical reviewer |

---

## Architecture Decision Records

### ADR-009: Structured Outputs over Tool Calling
**Status:** Accepted
**Context:** Agents need to produce structured data. Two approaches exist: structured outputs (JSON schema) or tool calling (function calling).
**Decision:** Use structured outputs (response_format) as the primary pattern. Tools are only used for data retrieval (DB queries), not for output formatting.
**Rationale:** Structured outputs are simpler, cheaper (fewer tokens), more reliable, and easier to validate. Tool calling adds unnecessary complexity when the output is known at prompt time.

### ADR-010: gpt-4o-mini for Extraction, gpt-4o for Reasoning
**Status:** Accepted
**Context:** Different tasks have different quality and cost requirements.
**Decision:** Medical extraction and adherence messages use gpt-4o-mini. Patient chat, emergency triage, and doctor summaries use gpt-4o.
**Rationale:** Extraction is pattern-matching, best done cheaply. Chat and emergency require nuanced reasoning. This tiering saves ~40% in costs while maintaining quality where it matters.

### ADR-011: Pre-Loaded Context over Tool Calling
**Status:** Accepted
**Context:** Agents need patient data to generate responses.
**Decision:** All patient data is loaded into state before any LLM call. No tool calling for data retrieval during LLM execution.
**Rationale:** Pre-loading is faster (parallel DB queries), more reliable (no tool call failures mid-generation), and prevents the LLM from accessing data it shouldn't. Tools for data retrieval add latency and failure modes.

### ADR-012: Prompt Library as Markdown Files
**Status:** Accepted
**Context:** Prompt versioning, review, and management.
**Decision:** All prompts stored as standalone Markdown files in `backend/prompts/` with YAML frontmatter. Loaded dynamically by `PromptLoader`.
**Rationale:** Markdown is human-readable, diffable in git, reviewable in PRs, and independent of Python code. Frontmatter enables schema validation and metadata tracking.

### ADR-013: Retry Budget with Degradation
**Status:** Accepted
**Context:** Retries can cause unbounded latency in production.
**Decision:** Implement a 15-second retry budget per request. After budget is exhausted, degrade to fallback model or rule-based response rather than continuing to retry.
**Rationale:** Protects p95 latency by bounding worst-case execution time. Degraded response is better than timeout.

### ADR-014: Always-HIGH Safety Default
**Status:** Accepted
**Context:** When emergency triage fails, what risk level should be returned?
**Decision:** If the emergency agent cannot determine risk level (LLM failure, timeout, error), default to HIGH.
**Rationale:** Safety-critical system. Defaulting to HIGH ensures patients get medical attention when the system is uncertain. False positives are safer than false negatives.
