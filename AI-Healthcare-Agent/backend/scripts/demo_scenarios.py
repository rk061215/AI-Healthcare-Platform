"""5 Demo Scenario Scripts for the AI Healthcare Platform.

Usage:
    python scripts/demo_scenarios.py          # runs all 5
    python scripts/demo_scenarios.py -s 1     # run specific scenario
    python scripts/demo_scenarios.py -i       # interactive mode (prompt between steps)
"""

import argparse
import os
import sys
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"


def c(text: str, *codes: str) -> str:
    return "".join(codes) + text + RESET


def header(num: int, title: str) -> None:
    bar = "=" * 72
    print()
    print(c(bar, CYAN, BOLD))
    print(c(f"  SCENARIO {num}: {title}", CYAN, BOLD))
    print(c(bar, CYAN, BOLD))
    print()


def step(label: str) -> None:
    print(c(f"\n  >>> {label}", YELLOW, BOLD))


def ok(label: str, detail: str = "") -> None:
    icon = c("OK", GREEN, BOLD)
    msg = f"  {icon} {label}"
    if detail:
        msg += c(f"  -- {detail}", DIM)
    print(msg)


def info(label: str, indent: int = 2) -> None:
    prefix = " " * indent
    print(f"{prefix}{c(label, DIM)}")


def divider() -> None:
    print(c("  " + "-" * 68, DIM))


def wait_for_user(interactive: bool) -> None:
    if interactive:
        try:
            input(c("\n  Press Enter to continue ...", MAGENTA, DIM))
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
    else:
        time.sleep(1.2)


# ---------------------------------------------------------------------------
# Path setup -- allow `python scripts/demo_scenarios.py` from anywhere
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

os.environ.setdefault("OCR_USE_MOCK", "True")
os.environ.setdefault("OCR_ENABLED", "True")
os.environ.setdefault("JWT_SECRET_KEY", "demo-secret-key-not-for-production")
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-demo")
os.environ.setdefault("OCR_ENGINE", "tesseract")

# ---------------------------------------------------------------------------
# Imports (lazy where possible for clarity)
# ---------------------------------------------------------------------------
import app.tools  # noqa: F401, E402 -- registers all tools into global registry
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.database.enums import MedicineRoute, ReportStatus
from app.core.seed import SeedData
from app.services.auth_service import AuthService
from app.services.report_service import ReportService
from app.services.medicine_service import MedicineService
from app.services.chat_service import ChatService as DBChatService
from app.services.doctor_service import DoctorService
from app.services.appointment_service import AppointmentService
from app.services.summary_service import SummaryService
from app.services.patient_service import PatientService
from app.tools.tool_service import ToolService
from app.tools.tool_selector import ToolSelector
from app.memory import MemoryService
from app.memory.models import MemoryType


# ---------------------------------------------------------------------------
# Database fixture
# ---------------------------------------------------------------------------
_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _get_db() -> Session:
    return _SessionLocal()


def _init_db() -> Session:
    Base.metadata.create_all(bind=_engine)
    db = _get_db()
    seeder = SeedData(db)
    seeder.seed_all()
    return db


# ---------------------------------------------------------------------------
# Helpers for pretty-printing service results
# ---------------------------------------------------------------------------
def _show_patient(user: dict) -> None:
    ok(f"Patient: {user.get('full_name', '?')}  ({user.get('email', '?')})")
    info(f"ID: {user.get('id', '?')}")


def _show_doctor(user: dict) -> None:
    ok(f"Doctor: {user.get('full_name', '?')}  ({user.get('email', '?')})")
    info(f"Specialization: {user.get('specialization', '?')}")


def _show_report(report) -> None:
    ok(f"Report: {report.title or 'Untitled'}")
    info(f"ID: {report.id}  |  Status: {report.status}  |  Type: {report.file_type}")


def _show_medicines(medicines: list) -> None:
    if not medicines:
        info("No medicines found.")
        return
    divider()
    for m in medicines:
        info(f"- {m.name}  {m.dosage}  |  {m.frequency}  |  {m.instructions or ''}")
    divider()


# ===================================================================
# SCENARIO 1 -- Patient Uploads Prescription
# ===================================================================
def scenario_1(db: Session, interactive: bool) -> None:
    header(1, "Patient Uploads Prescription")

    # --- login / register patient ---
    step("Register a new patient")
    auth = AuthService(db)
    patient = auth.register_patient(
        email="demo-patient@example.com",
        password="Demo1234!",
        full_name="Demo Patient",
        phone="+15551234567",
    )
    _show_patient(patient["user"])
    pid = patient["user"]["id"]
    wait_for_user(interactive)

    # --- create a mock prescription file ---
    step("Create a mock prescription file")
    upload_dir = Path(_BACKEND_DIR, "uploads")
    upload_dir.mkdir(exist_ok=True)
    mock_file = upload_dir / f"prescription_{uuid.uuid4().hex[:8]}.txt"
    mock_file.write_text(
        "Prescription\n"
        "Patient: Demo Patient\n"
        "Date: 2026-07-16\n"
        "Rx: Metformin 500 mg -- 1 tablet twice daily with meals\n"
        "Rx: Lisinopril 10 mg -- 1 tablet once daily\n"
        "Rx: Atorvastatin 20 mg -- 1 tablet at bedtime\n"
    )
    ok(f"Mock prescription created: {mock_file.name}")
    wait_for_user(interactive)

    # --- upload the prescription as a report ---
    step("Upload prescription as a report")
    report_svc = ReportService(db)
    report = report_svc.create_report(
        patient_id=pid,
        file_path=str(mock_file),
        file_type="text/plain",
        title="Demo Prescription Upload",
    )
    ok("Report record created", "pending")
    wait_for_user(interactive)

    # --- simulate OCR processing ---
    step("System processes OCR on the prescription")
    ocr_text = (
        "Patient: Demo Patient\n"
        "Date: 2026-07-16\n"
        "Medications:\n"
        "- Metformin 500 mg\n"
        "- Lisinopril 10 mg\n"
        "- Atorvastatin 20 mg\n"
    )
    extracted = {
        "medications": [
            {"name": "Metformin", "dosage": "500 mg", "frequency": "twice daily"},
            {"name": "Lisinopril", "dosage": "10 mg", "frequency": "once daily"},
            {"name": "Atorvastatin", "dosage": "20 mg", "frequency": "once daily at bedtime"},
        ]
    }
    report_svc.update_report_status(
        report_id=str(report.id),
        status="completed",
        ocr_text=ocr_text,
        extracted_data=extracted,
    )
    ok("OCR processing complete", "completed")
    _show_report(report_svc.get_report(str(report.id)))
    wait_for_user(interactive)

    # --- create medicine records from extraction ---
    step("Save extracted medicines to the database")
    med_svc = MedicineService(db)
    medicines_created = []
    for med in extracted["medications"]:
        m = med_svc.create_medicine({
            "report_id": report.id,
            "patient_id": uuid.UUID(pid),
            "name": med["name"],
            "dosage": med["dosage"],
            "frequency": med["frequency"],
            "route": MedicineRoute.ORAL,
            "instructions": f"Take {med['frequency']}",
            "start_date": date.today(),
            "is_active": True,
        })
        medicines_created.append(m)
    ok(f"{len(medicines_created)} medicines extracted and saved")
    _show_medicines(medicines_created)
    wait_for_user(interactive)

    ok("Scenario 1 complete -- prescription uploaded, OCR processed, medicines extracted")


# ===================================================================
# SCENARIO 2 -- Patient Asks Medication Questions
# ===================================================================
def scenario_2(db: Session, interactive: bool) -> None:
    header(2, "Patient Asks Medication Questions")

    # --- get the seeded patient ---
    step("Set up patient with existing report and medicines")
    auth = AuthService(db)
    patient = auth.login(email="alice@example.com", password="TestPass123!", role="patient")
    pid = patient["user"]["id"]
    _show_patient(patient["user"])

    med_svc = MedicineService(db)
    meds = med_svc.get_active_medicines(pid)
    _show_medicines(meds)
    wait_for_user(interactive)

    # --- Patient question #1 ---
    step('Patient asks: "What medications am I taking?"')
    answer_lines = [
        "Based on your active prescriptions, you are currently taking the following medications:",
    ]
    for m in meds:
        answer_lines.append(f"  - {c(m.name, BOLD)} {m.dosage} -- {m.frequency}")
    answer_lines.append("")
    answer_lines.append(c("Citations:", DIM))
    answer_lines.append(c("  [1] Prescription record -- Lisinopril 10 mg", DIM))
    answer_lines.append(c("  [2] Prescription record -- Atorvastatin 20 mg", DIM))
    answer_lines.append(c("  [3] Prescription record -- Metformin 500 mg", DIM))
    print("\n".join(answer_lines))

    chat_svc = DBChatService(db)
    chat_svc.save_message(pid, "user", "What medications am I taking?")
    chat_svc.save_message(pid, "assistant", "\n".join(answer_lines))
    wait_for_user(interactive)

    # --- Patient follow-up ---
    step('Patient asks follow-up: "When should I take Metformin?"')
    metformin = [m for m in meds if "metformin" in m.name.lower()]
    if metformin:
        m = metformin[0]
        follow_up = (
            f"You should take {c(m.name, BOLD)} {m.dosage} {m.frequency.lower()}.\n"
            f"{m.instructions or ''}\n\n"
            f"{c('Citations:', DIM)}\n"
            f"  {c('[1] Prescription record for Metformin 500 mg', DIM)}"
        )
        print()
        print(follow_up)

        chat_svc.save_message(pid, "user", "When should I take Metformin?")
        chat_svc.save_message(pid, "assistant", follow_up)
    wait_for_user(interactive)

    # --- show conversation history ---
    step("Conversation history")
    history = chat_svc.get_history(pid, limit=10)
    divider()
    for h in history:
        role_label = c("PATIENT", CYAN) if h.role == "user" else c("ASSISTANT", GREEN)
        preview = h.message[:80] + "..." if len(h.message) > 80 else h.message
        print(f"  {role_label}: {preview}")
    divider()
    wait_for_user(interactive)

    ok("Scenario 2 complete -- medication Q&A with citations and follow-up")


# ===================================================================
# SCENARIO 3 -- Follow-up Using Memory
# ===================================================================
def scenario_3(db: Session, interactive: bool) -> None:
    header(3, "Follow-up Using Memory")

    step("Set up patient with prior conversation history in memory")
    auth = AuthService(db)
    patient = auth.login(email="alice@example.com", password="TestPass123!", role="patient")
    pid = patient["user"]["id"]
    _show_patient(patient["user"])

    # Seed memory with prior context about cholesterol
    memory_svc = MemoryService()
    session_id = "demo-session-cholesterol"

    memory_svc.remember(
        session_id=session_id,
        content={
            "turn_number": 1,
            "query": "What were my cholesterol results?",
            "answer": "Your total cholesterol was 180 mg/dL with HDL of 55 and LDL of 110.",
            "query_type": "lab_result",
            "confidence": 0.92,
            "follow_up": False,
        },
        memory_type="conversation",
        importance=0.8,
    )
    memory_svc.remember(
        session_id=session_id,
        content={
            "turn_number": 2,
            "query": "Is my LDL too high?",
            "answer": "Your LDL of 110 mg/dL is slightly above the optimal target of <100 mg/dL. Dr. Sarah recommended continuing Atorvastatin and following a heart-healthy diet.",
            "query_type": "clinical_advice",
            "confidence": 0.88,
            "follow_up": True,
        },
        memory_type="conversation",
        importance=0.75,
    )
    memory_svc.remember(
        session_id=session_id,
        content={
            "turn_number": 3,
            "query": "Should I reduce my fat intake?",
            "answer": "Yes, Dr. Sarah advised reducing saturated fats and increasing soluble fiber to help lower LDL. She suggested oatmeal, nuts, and olive oil as part of a Mediterranean diet.",
            "query_type": "dietary_advice",
            "confidence": 0.85,
            "follow_up": True,
        },
        memory_type="conversation",
        importance=0.7,
    )
    ok("Prior conversation about cholesterol stored in memory (3 turns)")
    wait_for_user(interactive)

    # --- Patient asks about cholesterol ---
    step('Patient asks: "What did the doctor say about my cholesterol?"')
    memories = memory_svc.recall(session_id=session_id, memory_type="conversation", limit=5)
    print()
    print(c("  Retrieving from memory ...", DIM))

    relevant = [m for m in memories if "cholesterol" in str(m.content).lower() or "ldl" in str(m.content).lower()]
    if relevant:
        for entry in relevant:
            content = entry.content
            importance = entry.importance_label.value
            print(c(f"  [{importance.upper()}] Q: {content.get('query', '?')}", YELLOW))
            print(f"     A: {content.get('answer', '?')}")
    else:
        info("No relevant memories found.")

    # Synthesize answer from memory
    print()
    print(c(
        "  Based on your previous conversation, Dr. Sarah Chen noted:\n"
        "  - Your LDL of 110 mg/dL is slightly above the optimal target.\n"
        "  - She recommended continuing Atorvastatin 20 mg at bedtime.\n"
        "  - She advised a Mediterranean diet -- reduce saturated fats,\n"
        "    increase soluble fiber (oats, nuts, olive oil).\n"
        "  - Follow-up lipid panel scheduled at your next appointment.",
        BLUE,
    ))
    wait_for_user(interactive)

    ok("Scenario 3 complete -- memory-based follow-up with prior context")


# ===================================================================
# SCENARIO 4 -- Appointment Tool Execution
# ===================================================================
def scenario_4(db: Session, interactive: bool) -> None:
    header(4, "Appointment Tool Execution")

    step("Patient logs in and requests appointment booking")
    auth = AuthService(db)
    patient = auth.login(email="alice@example.com", password="TestPass123!", role="patient")
    pid = patient["user"]["id"]
    _show_patient(patient["user"])

    # Get the doctor (Dr. Sarah Chen)
    doctor_svc = DoctorService(db)
    patient_svc = PatientService(db)
    doctors = patient_svc.get_patient_doctors(pid)
    if not doctors:
        ok("No assigned doctor found; registering a demo doctor")
        doctor = auth.register_doctor(
            email="demo-doctor@example.com",
            password="Demo1234!",
            full_name="Dr. Demo Doctor",
            specialization="General Medicine",
            license_number="DEMO-001",
        )
        doctor_id = doctor["user"]["id"]
    else:
        doctor = doctors[0]
        doctor_id = str(doctor.id)
    _show_doctor({"full_name": doctor.full_name if hasattr(doctor, 'full_name') else doctor.get("full_name"),
                  "email": doctor.email if hasattr(doctor, 'email') else doctor.get("email"),
                  "specialization": doctor.specialization if hasattr(doctor, 'specialization') else doctor.get("specialization"),
                  "id": doctor_id})

    wait_for_user(interactive)

    # --- Tool Selector identifies intent ---
    step('ToolSelector identifies intent for: "Book an appointment with my doctor"')
    selector = ToolSelector()
    tool_name, action = selector.select("Book an appointment with my doctor")
    ok(f"Selected tool: {tool_name}, action: {action}")
    wait_for_user(interactive)

    # --- ToolService executes the booking ---
    step("ToolExecutor creates the appointment")
    scheduled_at = datetime.now(timezone.utc) + timedelta(days=3)
    scheduled_at = scheduled_at.replace(hour=10, minute=0, second=0, microsecond=0)

    tool_svc = ToolService()
    result = tool_svc.run(
        tool_type="appointment",
        action="book",
        user_id=pid,
        user_role="patient",
        patient_id=pid,
        doctor_id=doctor_id,
        parameters={
            "scheduled_at": scheduled_at,
            "title": "Medication Review",
            "description": "Review current medications and lab results",
            "duration_minutes": 30,
            "db_session": db,
        },
    )

    if result.success:
        appt_data = result.data
        ok("Appointment booked successfully")
        print(c(f"  Appointment ID: {appt_data.get('appointment_id', '?')}", CYAN))
        print(c(f"  Status:         {appt_data.get('status', '?')}", GREEN))

        appt_svc = AppointmentService(db)
        detail = appt_svc.get_appointment(str(appt_data["appointment_id"]), pid, "patient")
        print(c(f"  Doctor:         {detail.get('doctor_name', '?')}", CYAN))
        print(c(f"  Scheduled:      {detail.get('scheduled_at', '?')}", CYAN))
        print(c(f"  Duration:       {detail.get('duration_minutes', '?')} min", CYAN))
    else:
        print(c(f"  Appointment booking failed: {result.error_message}", RED))
    wait_for_user(interactive)

    ok("Scenario 4 complete -- appointment booked via tool execution pipeline")


# ===================================================================
# SCENARIO 5 -- Doctor Summary Generation
# ===================================================================
def scenario_5(db: Session, interactive: bool) -> None:
    header(5, "Doctor Summary Generation")

    step("Doctor logs in")
    auth = AuthService(db)
    doctor = auth.login(email="drsarah@example.com", password="DocPass456!", role="doctor")
    did = doctor["user"]["id"]
    _show_doctor(doctor["user"])
    wait_for_user(interactive)

    # --- View patient list ---
    step("Doctor views patient list")
    doctor_svc = DoctorService(db)
    patients = doctor_svc.get_doctor_patients(did)
    ok(f"{len(patients)} patients found")
    divider()
    for p in patients:
        info(f"- {p.full_name}  ({p.email})")
    divider()
    wait_for_user(interactive)

    # --- Select a patient ---
    step("Doctor selects a patient (Alice Johnson)")
    target_patient = patients[0] if patients else None
    if not target_patient:
        ok("No patients assigned; creating demo data")
        reg = auth.register_patient(
            email="demo-patient2@example.com",
            password="Demo1234!",
            full_name="Demo Patient Two",
        )
        pid = reg["user"]["id"]
        doctor_svc.assign_patient(did, pid)
        target_patient = type("obj", (), {"id": uuid.UUID(pid), "full_name": "Demo Patient Two"})()
    pid = str(target_patient.id)
    info(f"Selected patient: {target_patient.full_name}")
    wait_for_user(interactive)

    # --- Request AI summary ---
    step("Doctor requests AI summary of patient status")
    summary_svc = SummaryService(db)
    data = summary_svc.get_patient_summary_data(pid)

    print()
    print(c("  " + "+" + "=" * 54 + "+", CYAN))
    print(c("  |           PATIENT SUMMARY REPORT                    |", CYAN, BOLD))
    print(c("  " + "+" + "=" * 54 + "+", CYAN))

    print(c(f"\n  Patient:    {target_patient.full_name}", BOLD))
    print(f"  Generated:  {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    # Active medications
    medicines = data.get("medicines", [])
    print(c("  -- Active Medications --", YELLOW, BOLD))
    if medicines:
        for m in medicines:
            print(f"    {m.name} {m.dosage} -- {m.frequency}")
            print(f"      Route: {m.route.value if m.route else 'N/A'}  |  Instructions: {m.instructions or 'N/A'}")
            print(f"      Period: {m.start_date or 'N/A'} to {m.end_date or 'ongoing'}")
    else:
        info("    No active medications.")

    # Chat history
    chat_history = data.get("chat_history", [])
    print()
    print(c("  -- Recent Chat Activity --", YELLOW, BOLD))
    if chat_history:
        for ch in chat_history[-5:]:
            role = c("Patient", CYAN) if ch.role == "user" else c("Assistant", GREEN)
            preview = ch.message[:80] + "..." if len(ch.message) > 80 else ch.message
            print(f"    {role}: {preview}")
    else:
        info("    No chat history.")

    # Alert summary
    alerts = data.get("alerts", [])
    print()
    print(c("  -- Emergency Alerts --", YELLOW, BOLD))
    if alerts:
        for a in alerts:
            level = c(a.risk_level.value.upper(), RED) if a.risk_level.value == "high" else c(a.risk_level.value.upper(), YELLOW)
            print(f"    [{level}] {a.symptoms[:60]}...")
    else:
        info("    No alerts.")
    print()
    wait_for_user(interactive)

    ok("Scenario 5 complete -- doctor summary generated from reports + chat history")


# ===================================================================
# Main
# ===================================================================
SCENARIOS = [
    ("Patient Uploads Prescription", scenario_1),
    ("Patient Asks Medication Questions", scenario_2),
    ("Follow-up Using Memory", scenario_3),
    ("Appointment Tool Execution", scenario_4),
    ("Doctor Summary Generation", scenario_5),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Healthcare Demo Scenarios")
    parser.add_argument("-s", "--scenario", type=int, choices=range(1, 6),
                        help="Run a specific scenario (1-5)")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Wait for Enter between steps")
    args = parser.parse_args()

    print()
    print(c("+" + "=" * 68 + "+", CYAN, BOLD))
    print(c("|     AI HEALTHCARE FOLLOW-UP ASSISTANT -- DEMO           |", CYAN, BOLD))
    print(c("+" + "=" * 68 + "+", CYAN, BOLD))
    print(c(f"  Backend : {_BACKEND_DIR}", DIM))

    db = _init_db()
    print(c(f"  Database: SQLite in-memory (seeded)", DIM))
    print()

    if args.scenario:
        idx = args.scenario - 1
        title, fn = SCENARIOS[idx]
        print(c(f"  Running Scenario {args.scenario} only: {title}", MAGENTA))
        fn(db, args.interactive if args.interactive else False)
    else:
        interactive = args.interactive if args.interactive else False
        for i, (title, fn) in enumerate(SCENARIOS, 1):
            fn(db, interactive)
            if i < len(SCENARIOS):
                print()
                print(c(f"  Scenario {i} complete. Moving to Scenario {i + 1} ...", MAGENTA))
                wait_for_user(interactive)

    print()
    print(c("=" * 72, GREEN, BOLD))
    print(c("  ALL DEMO SCENARIOS COMPLETED SUCCESSFULLY", GREEN, BOLD))
    print(c("=" * 72, GREEN, BOLD))
    print()

    db.close()


if __name__ == "__main__":
    main()
