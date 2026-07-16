# End-to-End Workflow Validation

## Scenario 1: Upload Prescription → OCR → Parse → Chunk → Embed → Store → Q&A → Memory → Tool → Response

### Step 1: File Upload Endpoint

| Aspect | Detail |
|--------|--------|
| **API Endpoint** | `POST /api/v1/reports/upload` |
| **Key Class/Function** | `reports.py:upload_report()` → `ReportService.create_report()` |
| **Request** | `multipart/form-data` with `file` (`.pdf`, `.jpg`, `.jpeg`, `.png`; max `MAX_UPLOAD_SIZE_MB`) |
| **Auth** | `Depends(get_current_patient)` — JWT patient token required |
| **Flow** | Validate extension → read bytes → validate size → generate UUID → write to `settings.upload_path` → `ReportService.create_report()` persists DB row with `status="pending"` |
| **Response** | `{ "id": "uuid", "title": "...", "status": "pending", "uploaded_at": "ISO8601" }` |
| **Error Handling** | `ValidationException` for bad file type or oversized file; DB integrity errors propagate as 500 |

### Step 2: OCR Engine (Tesseract/Google Vision)

| Aspect | Detail |
|--------|--------|
| **API Endpoint** | `POST /api/v1/reports/{report_id}/process` |
| **Key Classes** | `OcrService.process_report()` → `OcrEngine.process_document()` |
| **OCR Providers** | Tesseract, Google Cloud Vision (selected via `settings.OCR_PROVIDER`; mock mode via `settings.OCR_USE_MOCK`) |
| **Flow** | Fetch report from DB → set `status=PROCESSING` → read file from disk → `OcrEngine.process_document(file_path, file_type, retry_count)` → returns `OcrJobResult{status, provider, confidence, pages_processed, full_text, extracted_data, preprocessing_applied}` |
| **Error Handling** | `NotFoundException` if report missing; `ValidationException` if OCR disabled; generic `Exception` caught → sets `status=FAILED` + `error_message`; retries via `retry_count` tracking |
| **Outcome** | `_save_ocr_result()` writes `ocr_text`, `ocr_confidence`, `ocr_provider`, `ocr_pages`, `extracted_data` to DB; `status=COMPLETED` or `FAILED` |

### Step 3: Medical Parser Extractor

| Aspect | Detail |
|--------|--------|
| **Key Functions** | `medical_parser/extractor.py:extract()` → `AIExtractor.extract()` with `RegexExtractor` fallback |
| **AI Extraction** | Uses `BaseProvider.generate_structured_output()` with prompt `medical/report_analysis`, retries 3x with exponential backoff, validates output against `MedicalReportSchema` Pydantic model |
| **Regex Fallback** | `RegexExtractor.extract()` uses regex patterns for patient name, DOB, doctor, hospital, diagnosis, medications (`name + dosage + instructions`), lab results (`test_name + value + unit`), follow-up date, doctor instructions |
| **Schema Output** | `MedicalReportSchema{document_type, patient_name, date_of_birth, document_date, doctor_name, hospital_name, diagnosis, medications[], lab_results[], follow_up_date, doctor_instructions, notes}` |
| **Context Tracking** | `ExtractionContext` carries `source` (AI/REGEX), `raw_ai_response`, `field_sources`, `validation_errors` |
| **Error Handling** | `EmptyOCRError` for blank input; `RetryExhaustedError` after 3 AI failures; `RegexExtractorError` if both AI and regex fail |

### Step 4: Document Pipeline (Chunking)

| Aspect | Detail |
|--------|--------|
| **Key Classes** | `DocumentPipeline`, `FixedSizeChunker`, `RecursiveChunker`, `MedicalSectionChunker`, `SentenceChunker`, `SemanticChunker` |
| **Pipeline Stages** | `Clean` (whitespace/unicode normalization) → `Classify` (keyword scoring: prescription, lab_report, discharge_summary, radiology_report, consultation) → `Detect Sections` (regex: patient_info, diagnosis, medications, lab_results, doctor_notes, follow_up, vitals, prescriptions) → `Chunk` (configurable: fixed/recursive/medical_section/sentence/semantic) → `Enrich Metadata` |
| **Default Chunker** | Configurable via `DocumentPipelineConfig.chunker_type`; default is fixed-size chunking with configurable `chunk_size` and `chunk_overlap` |
| **Chunk Output** | `list[DocumentChunk]` with `chunk_id`, `document_id`, `text`, `ChunkMetadata{chunk_index, report_id, patient_id, document_type, section, page, source, language, provider, chunker_type, chunk_version, embedding_version, schema_version}` |
| **Error Handling** | `MalformedDocumentError` for empty input; `EmptyDocumentError` if cleaning yields nothing; `StageExecutionError` wraps unexpected exceptions; `ChunkingError` for invalid chunker type |

### Step 5: Embedding Service

| Aspect | Detail |
|--------|--------|
| **Key Classes** | `EmbeddingService`, `EmbeddingFactory`, `BaseEmbedding` |
| **Provider** | Gemini Embedding (default); OpenAI/Sentence Transformers scaffolded |
| **Methods** | `embed(text)` → `(vector[], EmbeddingMetadata)`, `embed_batch(texts[])` → `(vectors[][], EmbeddingMetadata[])`, `embed_query(text)` → `(vector[], EmbeddingMetadata)` |
| **Metadata** | `EmbeddingMetadata{provider, model, dimensions, embedding_version, schema_version, duration_ms}` |
| **Error Handling** | `BatchEmbeddingError` wraps provider batch failures; `EmbeddingFailureError` for single-embed failures |
| **Versioning** | Schema version tracking supports re-embedding migrations via `ReEmbeddingService` |

### Step 6: Vector Store (ChromaDB)

| Aspect | Detail |
|--------|--------|
| **Key Classes** | `VectorService`, `BaseVectorStore` (ChromaDB implementation), `VectorStoreFactory` |
| **Indexing** | `index_chunks(chunks[])`: embed batch → convert to `IndexableDocument[]` → `store.add_documents()` → returns `list[str]` of IDs |
| **Search** | `search(query, k, filter)` → embed query → `store.similarity_search(vector, k, filter)`; supports `SearchFilter{patient_id, report_id, document_type, section}` |
| **Patient-scoped Search** | `search_by_patient(patient_id, query, k)` — filters by patient |
| **Report-scoped Search** | `search_by_report(report_id, query, k)` — filters by report |
| **Health Check** | `health_check()` returns status of both vector store and embedding service |
| **Error Handling** | `DocumentOperationError` for indexing failure; `SearchError` for query embedding failure; connection errors propagate from ChromaDB adapter |

### Step 7: RAG Query/Answer

| Aspect | Detail |
|--------|--------|
| **Key Classes** | `RAGEngine`, `RAGRequest`, `RAGResponse`, `QueryProcessor`, `QueryClassifier`, `QueryRewriter`, `RetrievalOrchestrator`, `ResponseGenerator`, `CitationManager`, `Guardrails` |
| **Pipeline** | Query Processing → Classification → (Rewriting) → Retrieval + Context Building → Pre-guardrails → Generation → Post-guardrails → Citations → Safety Disclaimer |
| **RAGRequest Fields** | `query`, `patient_id`, `report_id`, `document_type`, `top_k`, `temperature`, `max_tokens`, `enable_citations`, `conversation_history`, `context_strategy`, `metadata_filter` |
| **RAGResponse Fields** | `answer`, `citations` (CitationBlock), `query_type`, `guardrail_result`, `processing_time_ms`, `model`, `provider` |
| **Retrieval Orchestration** | `RetrievalOrchestrator.orchestrate()` returns `(retrieved: RetrievedDocs, context: BuiltContext)` with `retrieval_time_ms`, `build_time_ms`, `fragment_count`, `total_tokens` |
| **Guardrails** | Pre-generation: checks query and context for safety/hallucination risks; Post-generation: validates response against context and citations; applies safety disclaimer |
| **Error Handling** | `EmptyQueryError`/`QueryError` → graceful error response; `RAGError` → generic error response; guardrail failures → fallback message |

### Step 8: Memory Persistence

| Aspect | Detail |
|--------|--------|
| **Key Classes** | `MemoryService`, `BaseMemoryStore` (in-memory default, Redis/Postgres adapters), `MemoryExtractor`, `MemoryRetriever`, `MemorySummarizer`, `MemoryPruner` |
| **Memory Types** | Conversation, preference, document context (via `MemoryType` enum) |
| **Writing** | `extract_from_chat(session_id, query, answer, query_type, confidence, turn_number, follow_up)` → `MemoryExtractor` builds entry → `remember()` validates via `RetentionPolicy`, applies `ExpiryPolicy`, stores via `store.store()` |
| **Reading** | `recall(session_id, memory_type, limit)` → `MemoryRetriever.retrieve()` → applies retention/expiry filters |
| **Pruning** | `prune_session()` uses importance threshold; `prune_expired()` removes TTL-expired entries |
| **Summarization** | `summarize_session()` uses `MemorySummarizer` when turn count exceeds `summarization_threshold` |
| **Error Handling** | `MemoryFullError` when session exceeds `max_memories_per_session`; `MemoryNotFoundError` for missing entry deletion; `SessionNotFoundError` for clear/recall on nonexistent session |

### Step 9: Tool Calling Framework

| Aspect | Detail |
|--------|--------|
| **Key Classes** | `ToolService`, `ToolRegistry`, `ToolFactory`, `ToolExecutor`, `ToolSelector`, `BaseTool` |
| **Registered Tools** | `MedicationTool` (actions: schedule, explain), `AppointmentTool` (actions: book, cancel, reschedule, list), `ReportTool` (actions: list, summarize, metadata), `PatientTool`, `DoctorTool` |
| **Selection** | `ToolSelector.select(query)` → keyword matching → returns `(tool_type, action)` |
| **Execution Flow** | `ToolService.run_from_query(query, user_id, role, patient_id)` → `selector.select()` → `ToolFactory.create()` → `ToolExecutor.execute()` → `tool.validate()` → `tool.authorize()` → `tool.execute()` → `ToolResult` |
| **ToolResult** | `{success, data, error_message, tool_name, action, duration_ms, metadata}` |
| **LangGraph Integration** | `tool_selector_node` → `need_tool_edge` → `tool_executor_node` → results stored in `state.tool_result` |
| **Error Handling** | `ToolNotFoundError` → error ToolResult; `ToolSelectorError` → graceful degradation; `ToolValidationError` / `ToolAuthorizationError` → per-tool validation failures; exceptions → `ToolResult.error_factory()` |

### Step 10: Response Generation

| Aspect | Detail |
|--------|--------|
| **Key Classes** | `ResponseGenerator` (RAG-level), `ResponseFormatter` (chat-level), `ConfidenceCalculator` |
| **RAG Generation** | `ResponseGenerator.generate(query, context, temperature, max_tokens)` → LLM call → returns answer string |
| **Chat Formatting** | `ResponseFormatter.format_answer(answer, confidence, citations, suggested_questions, query_type, is_follow_up)` → enriches with confidence badges, citation markers, suggested follow-ups |
| **Confidence Calculation** | `ConfidenceCalculator.calculate(retrieval_scores, num_citations, guardrail_passed, guardrail_failures, answer_text, has_sufficient_context)` → `ConfidenceScore{overall, per_citation, ...}` |
| **Citation Format** | Each citation: `{source, snippet, confidence, document_id, chunk_id, section}` |
| **Final API Response** | `POST /api/v1/chat/message` returns `ChatResponse{reply, sources[], metadata{session_id, confidence, query_type, processing_time_ms, graph_executed}}` |
| **Error Handling** | `EmptyQuestionError` at chat layer; `ChatError` wrapping graph failures; graceful answer fallback for RAG errors |

---

## Scenario 2: Lab Report Upload → Medical Extraction → Follow-up Questions → Doctor Summary

### Step 1: Lab Report Upload

Same upload pipeline as Scenario 1 (Steps 1–2): `POST /api/v1/reports/upload` → OCR processing via `POST /api/v1/reports/{id}/process`.

### Step 2: Medical Extraction (Lab-Specific)

| Aspect | Detail |
|--------|--------|
| **Key Classes** | `Extractor.extract()` → `MedicalReportSchema` with `lab_results[]` |
| **Lab Data Schema** | `LabResultExtracted{test_name, value, unit, reference_range}` populated from `MedicalReportSchema.lab_results` |
| **Classification** | `SimpleDocumentClassifier` identifies `"lab_report"` via keywords (lab, laboratory, test result, reference range, specimen, hgba1c, glucose, etc.) |
| **Confidence Processing** | Overall OCR confidence from OcrEngine; per-field confidence from `ConfidenceEngine`; extracted into `MedicalReportResult` with `ConfidenceField<T>` wrappers |
| **Output** | `extracted_data` column on Report table stores the full `MedicalReportResult` JSON |

### Step 3: Follow-up Question Generation

| Aspect | Detail |
|--------|--------|
| **Key Classes** | `QuestionSuggester`, `ChatService` |
| **Trigger** | `POST /api/v1/chat/message` after report processing; session bound to report via `report_id` |
| **Suggestion Logic** | `QuestionSuggester.suggest(document_sections, recent_questions, document_has_diagnosis, has_medication, has_lab_results, has_follow_up)` → generates contextually relevant questions |
| **Example Lab Follow-ups** | "Which lab values are abnormal?", "What is the trend in my glucose levels?", "Should I be concerned about my LDL level?" |
| **Response** | Included in `ChatResponse.suggested_questions[]` |

### Step 4: Doctor Summary Generation

| Aspect | Detail |
|--------|--------|
| **API Endpoint** | `GET /api/v1/doctor-dashboard/summaries` → `DoctorDashboardService.get_ai_summaries()` |
| **Summary Content** | AI-generated patient summary combining: extracted lab values, flagged abnormalities, recommended follow-up timeline, medication adherence status |
| **Data Sources** | Report extracted data, chat history, medicine adherence records, appointment history |
| **Output** | Paginated list of summary objects with patient context, key findings, risk indicators |
| **Error Handling** | `NotFoundException` if patient/summary missing; pagination bounds checked |

---

## Scenario 3: Medication Reminder Workflow

### Step 1: Login

| Aspect | Detail |
|--------|--------|
| **API Endpoint** | `POST /api/v1/auth/login` |
| **Key Function** | `AuthService.login(email, password, role, remember_me)` |
| **Flow** | Validate credentials → JWT generation (access + refresh tokens) → `AuthResponse{access_token, refresh_token, token_type, expires_in, user{id, email, role}}` |
| **Role** | Patient role for portal access |
| **Error Handling** | Invalid credentials → 401; disabled account → 403 |

### Step 2: Dashboard

| Aspect | Detail |
|--------|--------|
| **API Endpoint** | `GET /api/v1/dashboard/overview` |
| **Key Function** | `DashboardService.get_overview(patient_id)` |
| **Flow** | Fetch patient profile → upcoming appointments → active medicines → recent reports → adherence stats → AI status → `DashboardOverview` |
| **Medicine Section** | `GET /api/v1/dashboard/medicines` → `DashboardService.get_medicines()` → returns paginated `MedicineWithSchedule[]` with names, dosages, frequencies, adherence percentage |
| **Adherence Tracking** | Tracked via `Medicine.adherence` field and `ReminderHistoryItem` records |
| **AI Status** | `GET /api/v1/dashboard/ai-status` → `AIStatusCard` with summary of AI-generated insights for the day |

### Step 3: Adherence Tracking

| Aspect | Detail |
|--------|--------|
| **Key Service** | `MedicineService.get_active_medicines(patient_id)` → `MedicineRepository.get_active_by_patient()` |
| **Data Model** | `Medicine{id, patient_id, name, dosage, frequency, duration, route (enum), instructions, start_date, end_date, adherence (float)}` |
| **Reminder History** | `GET /api/v1/dashboard/reminders` → `DashboardService.get_reminder_history()` → paginated `ReminderHistoryItem[]` with timestamp, medicine, status (taken/skipped/pending) |
| **Tool Integration** | `MedicationTool._schedule()` → returns active medicines list for AI to discuss adherence with patient |

### Step 4: Reminder Scheduling

| Aspect | Detail |
|--------|--------|
| **Tool Action** | `MedicationTool(action="schedule")` → returns `{patient_id, medications[], total}` |
| **AI Conversation** | Patient asks via `POST /api/v1/chat/message` → LangGraph routes through `tool_selector_node` → keyword match on "remind", "schedule", "medication" → `tool_executor_node` runs `MedicationTool` → results fed to `response_generator_node` |
| **Memory** | `persist_memory_node` stores the medication discussion context → available on next interaction |
| **Error Handling** | Tool errors return `ToolResult.error_factory()` → `response_generator` produces helpful fallback message |

---

## Scenario 4: Appointment Booking Workflow

### Step 1: Doctor Search

| Aspect | Detail |
|--------|--------|
| **API Endpoint** | `GET /api/v1/doctors/me` (for assigned), or via dashboard |
| **Key Service** | `DoctorService.get_doctor(doctor_id)`, `DoctorService.get_doctor_patients(doctor_id)` |
| **Patient-side** | `GET /api/v1/patients/me/doctors` → returns assigned doctors with `{id, full_name, specialization}` |
| **Error Handling** | Patient with no assigned doctors returns empty list |

### Step 2: Availability

| Aspect | Detail |
|--------|--------|
| **API Endpoint** | `GET /api/v1/appointments/doctor/available-slots?doctor_id=X&date=YYYY-MM-DD` |
| **Key Function** | `AppointmentService.get_available_slots(doctor_id, date)` |
| **Doctor-side** | `POST /api/v1/appointments/doctor/slots` → doctor sets availability slots |
| **Flow** | Subscribe patient to doctor → query posted availability → return open time slots |
| **Error Handling** | Invalid doctor_id → 404; past date → validation error |

### Step 3: Book Appointment

| Aspect | Detail |
|--------|--------|
| **API Endpoint** | `POST /api/v1/appointments` |
| **Schema** | `AppointmentCreate{doctor_id, scheduled_at, title, description, duration_minutes, timezone}` |
| **Key Function** | `AppointmentService.create_appointment(data, user_id, role)` |
| **Flow** | Validate slot availability → create appointment with `status=scheduled` → return `AppointmentResponse{id, patient_id, doctor_id, title, scheduled_at, duration_minutes, status, timezone}` |
| **Tool Path** | Patient says "Book an appointment with Dr. X" → LangGraph `tool_selector_node` → `AppointmentTool(action="book")` → `AppointmentService.create_appointment()` |
| **Error Handling** | Double-booking prevention via slot validation; `NotFoundException` for invalid doctor_id |

### Step 4: Confirm Appointment

| Aspect | Detail |
|--------|--------|
| **API Endpoint** | `POST /api/v1/appointments/{id}/confirm` |
| **Key Function** | `AppointmentService.confirm_appointment(id, user_id, role)` |
| **Flow** | Update appointment status from `scheduled` to `confirmed` |
| **Error Handling** | 404 if appointment not found; 403 if unauthorized user; 400 if appointment already confirmed/cancelled |

### Step 5: Reschedule/Cancel

| Aspect | Detail |
|--------|--------|
| **Reschedule** | `POST /api/v1/appointments/{id}/reschedule` with `AppointmentReschedule{scheduled_at, reason}` → `AppointmentService.reschedule_appointment()` → updates time + sets reschedule reason |
| **Cancel** | `POST /api/v1/appointments/{id}/cancel` with `AppointmentCancel{reason}` → `AppointmentService.cancel_appointment()` → sets `status=cancelled` |
| **Audit Trail** | `GET /api/v1/appointments/{id}/audit` → `AppointmentService.get_audit_logs()` → returns full change history |
| **Reminder** | `GET /api/v1/appointments/{id}/remind` → sends notification |
| **Tool Path** | AI conversation → `AppointmentTool(action="reschedule"|"cancel")` → parameters from chat context |
| **Error Handling** | Cannot reschedule/cancel already past appointments; authorization enforced via role checks |

---

## Scenario 5: Multi-turn Medical Conversation

### Step 1: Initial Query

| Aspect | Detail |
|--------|--------|
| **API Endpoint** | `POST /api/v1/chat/message` |
| **Request Schema** | `ChatMessageRequest{message, session_id?, report_id?, document_type?, enable_citations?, top_k?, temperature?, max_tokens?}` |
| **Key Flow** | `DbChatService.save_message(patient_id, "user", message)` → `ChatService.ask(ChatRequest)` → `MedicalQAGraph.execute(GraphState)` |
| **Graph Initialization** | `_get_graph()` → `registry.get("medical_qa")` → `MedicalQAGraph.initialize()` → lazy singleton cached globally |

### Step 2: Memory Retrieval (Load Memory Node)

| Aspect | Detail |
|--------|--------|
| **Node** | `load_memory_node` |
| **Function** | `memory_service.recall(session_id, limit=20)` → returns up to 20 previous `MemoryEntry` objects |
| **State Update** | `state.memory_entries[]` populated with `{memory_id, memory_type, content, importance, created_at}` |
| **Edge Cases** | Gracefully handles missing `memory_service` or `session_id` with empty result |
| **Error Handling** | Exceptions caught → `state.errors[]` appended, `state.memory_entries = []` |

### Step 3: Graph Execution (Medical QA Node)

| Aspect | Detail |
|--------|--------|
| **Node** | `medical_qa_node` |
| **Function** | LLM-powered medical Q&A using session memory + query context |
| **Query Type** | Determined by `QueryClassifier` (medication, diagnosis, lab, appointment, general) |
| **State** | `state.rag_response{answer, query_type, processing_time_ms, model, provider}` |
| **Conditional Routing** | After QA → `tool_selector_node` evaluates `need_tool_edge` → if tool needed → `tool_executor_node` |
| **Conditional Retrieval** | After tools → `need_retrieval_edge` → if retrieval needed → `retriever_node` + `context_builder_node` |

### Step 4: Tool Calling

| Aspect | Detail |
|--------|--------|
| **Node** | `tool_selector_node` + `tool_executor_node` |
| **Tool Selector** | Keyword-based detection: "schedule", "app appointment", "book", "reschedule", "cancel", "remind", "medication" → sets `state.need_tool = True` |
| **Tool Executor** | `ToolService.run_from_query(query, patient_id, session_id)` → `ToolSelector.select()` → `ToolFactory.create()` → `ToolExecutor.execute()` → result stored in `state.tool_result{success, data, error, tool_name, action, duration_ms}` |
| **Domain Tools** | Medication (schedule/explain), Appointment (book/cancel/reschedule/list), Report (list/summarize/metadata), Patient, Doctor |
| **Error Handling** | Node exceptions → `state.errors[]` appended; tool failures → `ToolResult.error_factory()` with descriptive message |

### Step 5: Response Generation

| Aspect | Detail |
|--------|--------|
| **Node** | `response_generator_node` |
| **Function** | `ResponseGenerator.generate()` or `ResponseFormatter.format_answer()` |
| **Input** | `state.rag_response`, `state.retrieved_evidence`, `state.tool_result`, `state.memory_entries`, `state.conversation_history` |
| **Output** | `state.final_response` (formatted answer), citations from `retrieved_evidence` |
| **Confidence** | `ConfidenceCalculator.calculate()` → `state.confidence_score{overall, per_citation}` |
| **Citations** | Embedded as inline markers with source document references |

### Step 6: Memory Persist (Persist Memory Node)

| Aspect | Detail |
|--------|--------|
| **Node** | `persist_memory_node` |
| **Function** | `memory_service.extract_from_chat(session_id, query, answer, query_type, confidence=0.8)` → `MemoryExtractor` extracts structured entry → `remember()` stores |
| **State Update** | `state.persisted_memory_id` set to the stored entry ID |
| **Edge Cases** | Skips persist if no query/answer, no session_id, or memory_service unavailable |
| **Error Handling** | Exceptions caught → `state.errors[]` appended, `state.persisted_memory_id = ""` |

### Step 7: Follow-up with Context

| Aspect | Detail |
|--------|--------|
| **Chat History** | `GET /api/v1/chat/history` → `DbChatService.get_history(patient_id)` → returns all messages with role, message, metadata, timestamps |
| **Session Awareness** | `ChatService._get_or_create_session()` → reuses existing session for `session_id` continuity → enables follow-up detection via `SessionManager.is_follow_up_question()` |
| **Memory Carry-over** | Previous turns loaded by `load_memory_node` → available as context → QA can reference prior discussion |
| **Suggested Questions** | `QuestionSuggester` generates 4 contextual follow-ups based on document sections + recent questions |
| **Query Classification** | Follow-up detected → reranking adjusted → retrieval scope narrowed to conversation topic |
| **Edge Cases** | Session TTL expiry → auto-cleanup via `cleanup_expired_sessions()`; memory pruning when `max_memories_per_session` exceeded |
