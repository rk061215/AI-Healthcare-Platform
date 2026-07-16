# Demo Workflows

## Scenario 1: Upload Prescription → OCR → Parse → Chunk → Embed → Store → Q&A → Memory → Tool → Response

### Initial State
- PostgreSQL running with migrated schema
- ChromaDB running and empty
- Demo patient "John Doe" seeded (`POST /api/demo/seed`)
- Demo session active
- Predefined cardiology report scenario available in memory

### User Actions

| Step | Action | Details |
|------|--------|---------|
| 1 | Click **"Try Demo"** on login page | Auto-authenticates as demo patient |
| 2 | Navigate to **Reports** tab | Dashboard loads with empty reports list |
| 3 | Click **"Upload Report"** | File picker opens |
| 4 | Select `prescription.pdf` (or click "Use Demo Data") | Demo mode uses PREDEFINED_SCENARIOS random selection |
| 5 | Observe upload result | Confetti animation + report card with "Completed" badge |
| 6 | Navigate to **Chat** tab | Chat interface loads with session bound to report |
| 7 | Type "What medications are prescribed?" | Message sent to API |
| 8 | Review AI response | Answer with inline citations + confidence score + suggested questions |
| 9 | Click suggested question "Are there any abnormal findings?" | Follow-up sent to same session |
| 10 | Observe memory carry-over | AI references previous question in context |

### Expected AI Reasoning

```
1. User uploaded file → OCR extracted text
2. Classified as "prescription" via keyword scoring
3. AIExtractor called with prompt "medical/report_analysis"
4. Extracted MedicalReportSchema with medications, dosage, frequency
5. DocumentPipeline chunked text into FixedSizeChunks
6. EmbeddingService.embed_batch() vectorized each chunk
7. VectorService.index_chunks() stored in ChromaDB
8. User asks "What medications?" → RAGEngine.answer()
9. QueryProcessor → QueryClassifier ("medication") → RetrievalOrchestrator.search()
10. ChromaDB similarity search with patient_id filter
11. Retrieved chunks → ContextBuilder → ResponseGenerator
12. CitationManager extracted inline citations
13. ConfidenceCalculator scored response at 0.92
14. ResponseFormatter added suggested questions
15. PersistMemoryNode stored QA pair
```

### Expected Tool Execution
- **ReportTool (summarize)**: If user asks "Summarize my report"
- **MedicationTool (explain)**: If user asks "Tell me about lisinopril"
- **No tool** for general "What medications?" — answered via RAG retrieval directly

### Expected Memory Behavior

| Operation | Content Stored | Type |
|-----------|---------------|------|
| Upload | Report metadata + extracted_data in PostgreSQL | Document |
| Process | Chunk vectors in ChromaDB with patient_id metadata | Vector |
| Chat Turn 1 | QA pair: "What medications?" → answer + citations | Conversation |
| Chat Turn 2 | QA pair: "abnormal findings?" with follow_up flag | Conversation |

### Expected Citations

```json
[
  {
    "source": "Medication List",
    "snippet": "Lisinopril 10 mg once daily",
    "confidence": 0.95
  },
  {
    "source": "Diagnosis Section",
    "snippet": "Stage 1 Hypertension with mild LVH",
    "confidence": 0.93
  }
]
```

### Expected Outputs

**Upload Response:**
```json
{
  "id": "a1b2c3d4-...",
  "title": "prescription.pdf",
  "file_type": "pdf",
  "extracted_data": { "diagnosis": "Stage 1 Hypertension...", "medications": [...] },
  "ocr_confidence": 0.94,
  "suggestions": ["Review extracted data", "Ask about findings", "Export report"]
}
```

**Chat Response:**
```json
{
  "reply": "Based on your prescription, the following medications are prescribed:\n\n1. **Lisinopril** 10 mg — once daily for blood pressure\n2. **Atorvastatin** 20 mg — once daily for cholesterol\n\nThe medications align with your diagnosis of Stage 1 Hypertension. Please take as directed by your physician.",
  "sources": [
    { "source": "Medication List", "snippet": "Lisinopril 10 mg...", "confidence": 0.95 }
  ],
  "metadata": {
    "session_id": "abc123",
    "confidence": 0.92,
    "query_type": "medication",
    "processing_time_ms": 1247,
    "graph_executed": true
  },
  "suggested_questions": [
    "What are the side effects of these medications?",
    "Are there any abnormal findings?",
    "When should I follow up?"
  ]
}
```

---

## Scenario 2: Lab Report Upload → Medical Extraction → Follow-up Questions → Doctor Summary

### Initial State
- Demo patient "Jane Smith" seeded with lab_work scenario
- No lab reports in system yet
- Doctor "Dr. Gupta" assigned to patient

### User Actions (Patient View)

| Step | Action | Details |
|------|--------|---------|
| 1 | Login as demo patient | Auto-auth |
| 2 | Upload `lab_results.png` (or select "Lab Work" demo scenario) | CBC + metabolic panel |
| 3 | View extracted data | Structured table: WBC 6.2, Hgb 13.8, Glucose 98, etc. |
| 4 | Ask "Are all my lab values normal?" | Chat bound to lab report session |
| 5 | Ask "What does my glucose level mean?" | Follow-up within same session |
| 6 | Review confidence badges | Each citation has confidence score |

### User Actions (Doctor View)

| Step | Action | Details |
|------|--------|---------|
| 7 | Switch to Doctor login | Demo doctor credentials |
| 8 | Navigate to **Doctor Dashboard** | `GET /api/v1/doctor-dashboard/overview` |
| 9 | Click patient "Jane Smith" | Patient detail view with AI summary |
| 10 | View **AI Summary** card | DoctorDashboardService.get_ai_summaries() |
| 11 | Review **Alerts** tab | GET /api/v1/doctor-dashboard/alerts |

### Expected AI Reasoning

```
1. Lab report uploaded → OCR extracted text
2. Classifier identified "lab_report" via keywords
3. SimpleDocumentClassifier scored: lab_report=6, others=0-2
4. AIExtractor extracted structured lab values with MedicalReportSchema
5. RegexExtractor fallback would capture: test_name, value, unit
6. LabSection chunked separately for targeted retrieval
7. User asks "Are all values normal?" → RAGEngine.answer()
8. Retrieval filtered by patient_id + document_type="lab_report"
9. ResponseGenerator compares values to reference ranges
10. Returns "All results within normal limits" with per-metric confidence
```

### Expected Tool Execution
- **ReportTool (list)**: "Show me my lab reports"
- **ReportTool (metadata)**: "What is the file type of my report?"
- **No tool**: Direct RAG Q&A about lab values

### Expected Memory Behavior

| Operation | Content Stored |
|-----------|---------------|
| Lab upload | Extracted lab_result entries in ChromaDB |
| Q&A turn 1 | "Are values normal?" → "All normal" |
| Q&A turn 2 | "What does glucose mean?" → explanation (follow_up flag) |
| Doctor view | AI summary cached for doctor dashboard |

### Expected Citations

```json
[
  {
    "source": "Lab Results",
    "snippet": "Glucose: 98 mg/dL (normal range: 70-100)",
    "confidence": 0.97
  },
  {
    "source": "Diagnosis Section",
    "snippet": "All results within normal limits",
    "confidence": 0.94
  }
]
```

### Expected Outputs

**Chat Response for "Are all my lab values normal?":**
```json
{
  "reply": "Yes, all your lab values are within normal limits:\n\n| Test | Value | Reference Range | Status |\n|------|-------|-----------------|--------|\n| WBC | 6.2 x10⁹/L | 4.5-11.0 | ✅ Normal |\n| Hemoglobin | 13.8 g/dL | 12.0-16.0 | ✅ Normal |\n| Glucose | 98 mg/dL | 70-100 | ✅ Normal |\n| Creatinine | 0.9 mg/dL | 0.6-1.2 | ✅ Normal |\n\nNo follow-up is necessary based on these results. Continue routine annual screening as recommended.",
  "sources": [
    { "source": "Lab Results", "snippet": "WBC: 6.2 x10⁹/L", "confidence": 0.97 },
    { "source": "Lab Results", "snippet": "Glucose: 98 mg/dL", "confidence": 0.96 }
  ],
  "metadata": { "session_id": "...", "confidence": 0.94, "query_type": "lab_results" },
  "suggested_questions": [
    "Which values should I monitor regularly?",
    "What lifestyle changes can improve my health?",
    "When should I get tested again?"
  ]
}
```

**Doctor AI Summary Card:**
```json
{
  "patient_id": "...",
  "patient_name": "Jane Smith",
  "summary": "34-year-old female with all lab results within normal limits. No medications active. Last visit: CBC + CMP showing normal values. Next routine screening recommended in 12 months.",
  "risk_level": "low",
  "key_findings": [],
  "last_updated": "2026-07-16T10:30:00Z"
}
```

---

## Scenario 3: Medication Reminder Workflow

### Initial State
- Patient "John Doe" logged in
- 3 medications seeded: Lisinopril 10mg, Atorvastatin 20mg, Metformin 500mg
- All medications have adherence tracking enabled
- Reminder history has 7 days of data (mix of taken/skipped/pending)

### User Actions

| Step | Action | Details |
|------|--------|---------|
| 1 | Login as patient | Dashboard loads |
| 2 | View **Medicines** section on dashboard | `GET /api/v1/dashboard/medicines` — cards with name, dosage, frequency, adherence % |
| 3 | Click **Reminder History** | `GET /api/v1/dashboard/reminders` — timeline view |
| 4 | Navigate to Chat | Ask "What medications am I taking?" |
| 5 | Chat responds with medicine list | AI cites active medications |
| 6 | Ask "I missed my morning dose, what should I do?" | AI provides guidance based on medication type |
| 7 | View **Today's Schedule** | `GET /api/v1/dashboard/schedule` — shows medicine times + appointments |
| 8 | Visit **Health Timeline** | `GET /api/v1/dashboard/timeline?days=30` — adherence trends |

### Expected AI Reasoning

```
1. User asks "What medications am I taking?" → Chat POST
2. LangGraph: load_memory → medical_qa → tool_selector
3. tool_selector_node: matches keyword "medication" → need_tool=True
4. need_tool_edge → tool_executor_node
5. MedicationTool(action="schedule") called via ToolService.run_from_query()
6. MedicineService.get_active_medicines(patient_id) queries PostgreSQL
7. Returns 3 active medicines
8. tool_result → response_generator_node formats answer
9. persist_memory_node stores the medication discussion
```

### Expected Tool Execution
- **MedicationTool (schedule)**: Lists all active medicines when asked
- **MedicationTool (explain)**: Explains specific medicine when asked by name

### Expected Memory Behavior
- Medication discussion stored with memory_type="conversation"
- Adherence patterns extracted and stored as "preference" entries
- Missed dose question stored with follow_up for doctor alerting

### Expected Outputs

**Dashboard Medicines:**
```json
{
  "items": [
    { "id": "m1", "name": "Lisinopril", "dosage": "10 mg", "frequency": "Once daily",
      "adherence": 85, "next_dose": "2026-07-16T20:00:00Z" },
    { "id": "m2", "name": "Atorvastatin", "dosage": "20 mg", "frequency": "Once daily - night",
      "adherence": 92, "next_dose": "2026-07-16T21:00:00Z" },
    { "id": "m3", "name": "Metformin", "dosage": "500 mg", "frequency": "Twice daily",
      "adherence": 78, "next_dose": "2026-07-16T08:00:00Z" }
  ],
  "total": 3
}
```

**Chat: "What medications am I taking?":**
```json
{
  "reply": "You are currently prescribed 3 medications:\n\n1. **Lisinopril** 10 mg — Once daily (85% adherence)\n2. **Atorvastatin** 20 mg — Once daily at night (92% adherence)\n3. **Metformin** 500 mg — Twice daily (78% adherence)\n\nYour overall adherence is 85%. Would you like me to explain any of these medications or set up reminders?",
  "sources": [
    { "source": "Active Medications", "snippet": "Lisinopril 10 mg once daily", "confidence": 1.0 }
  ],
  "suggested_questions": [
    "Tell me about Lisinopril side effects",
    "What if I miss a dose of Metformin?",
    "How can I improve my adherence?"
  ]
}
```

---

## Scenario 4: Appointment Booking Workflow

### Initial State
- Patient "John Doe" logged in
- Doctor "Dr. Sarah Chen" (Cardiology) assigned to patient
- Doctor has posted availability slots for next week
- No existing appointments

### User Actions

| Step | Action | Details |
|------|--------|---------|
| 1 | Login as patient | Dashboard loads with empty appointments list |
| 2 | Navigate to **Appointments** tab | `GET /api/v1/appointments` — empty list |
| 3 | Click **"Book Appointment"** | Doctor selection dropdown (populated from `GET /api/v1/patients/me/doctors`) |
| 4 | Select Dr. Sarah Chen | Date picker shows available dates |
| 5 | Pick a date | `GET /api/v1/appointments/doctor/available-slots?doctor_id=X&date=YYYY-MM-DD` |
| 6 | Select time slot 10:00 AM | Booking form pre-fills |
| 7 | Click **Confirm Booking** | `POST /api/v1/appointments` |
| 8 | View confirmation | Appointment card shows with status "scheduled" |
| 9 | Click **Confirm** | `POST /api/v1/appointments/{id}/confirm` → status changes to "confirmed" |
| 10 | Ask in Chat "Reschedule my appointment to Friday" | LangGraph tool execution |

### Alternative: Chat-based Booking

| Step | Action | Details |
|------|--------|---------|
| 1 | Go to Chat | Type "I need to book an appointment" |
| 2 | AI responds with: "I can help! Which doctor?" | Tool selector detected intent |
| 3 | Reply "Dr. Sarah Chen" | AI calls AppointmentTool(action="book") |
| 4 | AI asks for preferred date/time | Conversational slot negotiation |
| 5 | Confirm details | Appointment created via API |
| 6 | Say "Cancel my appointment" | AppointmentTool(action="cancel") |

### Expected AI Reasoning

```
1. User says "Book appointment with Dr. Chen" → Chat POST
2. LangGraph: load_memory → medical_qa → tool_selector
3. tool_selector_node: matches "appointment", "book" → need_tool=True
4. tool_executor_node: AppointmentTool(action="book")
5. AI identifies missing parameters (date/time)
6. AI asks clarifying question → user provides date
7. Tool re-executed with complete parameters
8. AppointmentService.create_appointment() returns AppointmentResponse
9. response_generator formats confirmation
10. persist_memory stores appointment details
```

### Expected Tool Execution
- **AppointmentTool (book)**: Creates appointment when all params provided
- **AppointmentTool (list)**: Lists appointments on request
- **AppointmentTool (cancel)**: Cancels by appointment_id
- **AppointmentTool (reschedule)**: Reschedules with new datetime

### Expected Memory Behavior
- Appointment details stored in conversation memory
- Doctor preference remembered between sessions
- Cancellation reason stored for analytics

### Expected Outputs

**Appointment Created:**
```json
{
  "id": "apt-001",
  "patient_id": "...",
  "doctor_id": "...",
  "title": "Cardiology Follow-up",
  "scheduled_at": "2026-07-20T10:00:00Z",
  "duration_minutes": 30,
  "status": "scheduled",
  "timezone": "America/New_York"
}
```

**Chat: "Book appointment with Dr. Chen":**
```json
{
  "reply": "I'd be happy to book an appointment with Dr. Sarah Chen (Cardiology).\n\nCould you please tell me:\n1. What date would you prefer?\n2. What time works best for you?\n3. What is the reason for your visit?",
  "sources": [],
  "suggested_questions": ["Show me available slots", "Next Monday morning", "This Friday afternoon"]
}
```

**Chat: "Reschedule my Friday appointment":**
```json
{
  "reply": "I found your appointment with Dr. Chen on Friday, July 20 at 10:00 AM.\n\nWhat date and time would you like to reschedule to? Available slots this week:\n- Monday July 23: 9:00 AM, 10:00 AM, 2:00 PM\n- Wednesday July 25: 11:00 AM, 3:00 PM\n- Thursday July 26: 9:30 AM, 1:00 PM",
  "sources": [
    { "source": "Appointment", "snippet": "Dr. Sarah Chen, Jul 20, 10:00 AM", "confidence": 1.0 }
  ]
}
```

---

## Scenario 5: Multi-turn Medical Conversation

### Initial State
- Patient "John Doe" logged in
- Cardiology report already uploaded and processed
- 3 prior conversation turns in session memory
- Session ID `abc123-def456` active

### User Actions (Multi-turn Conversation)

| Turn | User Action | Expected AI Behavior |
|------|-------------|---------------------|
| 1 | "What does my report say about my heart?" | Load memory (empty) → QA → Retrieve report chunks → Format response with citations |
| 2 | "What is LVH?" | Load memory (turn 1 context) → Detect follow-up → QA with narrowed retrieval → Format |
| 3 | "Is this serious?" | Load memory (turns 1-2) → QA interprets "this" → Provides prognosis → Store |
| 4 | "What medications should I take?" | Load memory → QA → Tool selector (medication keyword) → MedicationTool → Format |
| 5 | "Book a follow-up for 3 months" | Load memory (3-month recommendation from report) → Tool selector → AppointmentTool → Format |
| 6 | "What did the doctor recommend again?" | Load memory → Recall all 5 prior turns → Summarize previous recommendations |

### Detailed Simulation

**Turn 1:**
```
User: "What does my report say about my heart?"

Graph: load_memory(empty) → medical_qa → tool_selector(no tool) → need_retrieval(true)
→ retriever_node: RAGEngine.answer() searches ChromaDB with patient_id filter
→ context_builder: compresses retrieved chunks
→ response_generator: "Your cardiology report shows Stage 1 Hypertension with mild LVH..."
→ persist_memory: stores QA pair

Expected Citations:
- "Ejection fraction: 55%, Mild left ventricular hypertrophy" (confidence 0.94)
- "Blood Pressure: 138/88 mmHg" (confidence 0.98)
```

**Turn 2:**
```
User: "What is LVH?"

Graph: load_memory(recalls turn 1: "LVH" mentioned) → medical_qa(interprets "LVH" using context)
→ tool_selector(no tool) → retriever(report chunks about LVH)
→ response_generator: "LVH stands for Left Ventricular Hypertrophy..."

Memory: New entry created with follow_up=True referencing turn 1
```

**Turn 3:**
```
User: "Is this serious?"

Graph: load_memory(recalls turns 1-2: LVH discussion) → medical_qa(resolves "this" = LVH)
→ No tool → Retrieval for prognosis context
→ response_generator: "With proper management including ACE inhibitors..."

Memory: Third entry in session; importance scored higher for clinical content
```

**Turn 5:**
```
User: "Book a follow-up for 3 months"

Graph: load_memory(recalls turn 1: 3-month recommendation) → medical_qa
→ tool_selector(keywords: "book") → need_tool_edge → tool_executor_node
→ AppointmentTool(action="book") with parameters extracted from chat + memory
→ response_generator: "I've booked your follow-up with Dr. Chen on October 16, 2026..."
→ persist_memory: stores appointment confirmation
```

**Turn 6:**
```
User: "What did the doctor recommend again?"

Graph: load_memory(recalls all 5 turns) → medical_qa
→ ContextBuilder loads full memory context
→ response_generator: "Based on our conversation, your doctor recommended: 1. ACE inhibitor therapy, 2. Low sodium diet, 3. Follow-up in 3 months..."

Memory: Compressed summarization triggered if threshold exceeded
```

### Expected AI Reasoning on Follow-up Detection

```
SessionManager.is_follow_up_question(session_id):
- Checks if session has existing Q&A pairs (>0 turns)
- Compares query pronouns ("this", "that", "it") to prior context
- Classifies follow-up: re-ranks with higher weight for session documents

QueryClassifier behavior:
- "What is LVH?" → query_type: "diagnosis" (follow-up variant)
- "Is this serious?" → query_type: "diagnosis" (context-dependent)
- "Book follow-up" → query_type: "appointment" (tool intent)
```

### Expected Memory State After 6 Turns

```json
{
  "session_id": "abc123-def456",
  "memory_entries": [
    { "turn": 1, "type": "conversation", "query": "What does my report say about my heart?",
      "importance": 0.7 },
    { "turn": 2, "type": "conversation", "query": "What is LVH?",
      "importance": 0.6, "metadata": { "follow_up": true } },
    { "turn": 3, "type": "conversation", "query": "Is this serious?",
      "importance": 0.8, "metadata": { "follow_up": true, "clinical_focus": "prognosis" } },
    { "turn": 4, "type": "conversation", "query": "What medications should I take?",
      "importance": 0.7 },
    { "turn": 5, "type": "conversation", "query": "Book a follow-up for 3 months",
      "importance": 0.9, "metadata": { "tool_used": "AppointmentTool", "appointment_id": "apt-002" } },
    { "turn": 6, "type": "conversation", "query": "What did the doctor recommend again?",
      "importance": 0.5, "metadata": { "follow_up": true, "summary_request": true } }
  ],
  "total_turns": 6,
  "summarized": false
}
```

### Expected Outputs

**Turn 1 Response:**
```json
{
  "reply": "Your cardiology consultation report indicates **Stage 1 Hypertension** with **mild Left Ventricular Hypertrophy (LVH)**. Key findings include:\n\n- **Blood Pressure**: 138/88 mmHg\n- **Ejection Fraction**: 55% (normal)\n- **Heart Rate**: 72 bpm (normal sinus rhythm)\n\nThe report recommends initiating an ACE inhibitor and follow-up in 3 months.",
  "sources": [
    { "source": "Report Findings", "snippet": "Blood Pressure: 138/88 mmHg", "confidence": 0.98 }
  ],
  "suggested_questions": [
    "What is LVH?",
    "What treatments are recommended?",
    "How serious is this?"
  ]
}
```

**Turn 6 Response:**
```json
{
  "reply": "Here's a summary of all recommendations from our conversation:\n\n1. **Medications**: ACE inhibitor (Lisinopril 10 mg) for blood pressure, Atorvastatin for cholesterol\n2. **Lifestyle**: Low sodium diet, regular exercise\n3. **Follow-up**: Appointment booked with Dr. Chen on October 16, 2026\n4. **Monitoring**: Routine lab work every 6 months for lipid profile and renal function\n\nIs there anything else you'd like to clarify about these recommendations?",
  "sources": [
    { "source": "Report Recommendations", "snippet": "Follow-up in 3 months, Low sodium diet", "confidence": 0.91 }
  ],
  "suggested_questions": [
    "What foods should I avoid on a low sodium diet?",
    "How do I take Lisinopril correctly?",
    "What symptoms should I watch for?"
  ]
}
```
