"""Tests for appointment CRUD with full production features."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.enums import AppointmentStatus
from app.models.appointment import Appointment, DoctorAvailability
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.patient_doctor import PatientDoctor

from tests.conftest import DOCTOR_PASSWORD, PATIENT_PASSWORD


def _register_patient(client: TestClient, email: str) -> tuple[str, str]:
    resp = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": email,
            "password": PATIENT_PASSWORD,
            "confirm_password": PATIENT_PASSWORD,
            "full_name": "Test Patient",
            "terms_accepted": True,
        },
    )
    data = resp.json()
    return data["access_token"], data["refresh_token"]


def _register_doctor(client: TestClient, email: str) -> tuple[str, str]:
    resp = client.post(
        "/api/v1/auth/register/doctor",
        json={
            "email": email,
            "password": DOCTOR_PASSWORD,
            "confirm_password": DOCTOR_PASSWORD,
            "full_name": "Test Doctor",
            "specialization": "Cardiology",
            "license_number": "LIC-12345",
        },
    )
    data = resp.json()
    return data["access_token"], data["refresh_token"]


def _get_user(client: TestClient, token: str) -> dict:
    return client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()


def _future(days: int = 7, hours: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days, hours=hours)).isoformat()


def _past(days: int = 7) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


# ─── CRUD Happy Path ────────────────────────────────────


def test_create_appointment(client: TestClient):
    pat_token, _ = _register_patient(client, "crpat@test.com")
    doc_token, _ = _register_doctor(client, "crdoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    resp = client.post(
        "/api/v1/appointments",
        json={
            "title": "Checkup",
            "doctor_id": doc["id"],
            "scheduled_at": _future(3),
        },
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Checkup"
    assert data["status"] == "scheduled"
    assert data["doctor_id"] == doc["id"]
    assert data["patient_id"] == pat["id"]


def test_list_patient_appointments(client: TestClient):
    pat_token, _ = _register_patient(client, "lpat@test.com")
    doc_token, _ = _register_doctor(client, "ldoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    client.post(
        "/api/v1/appointments",
        json={"title": "Visit", "doctor_id": doc["id"], "scheduled_at": _future(2)},
        headers={"Authorization": f"Bearer {pat_token}"},
    )

    resp = client.get("/api/v1/appointments", headers={"Authorization": f"Bearer {pat_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_list_doctor_appointments(client: TestClient):
    pat_token, _ = _register_patient(client, "ldp@test.com")
    doc_token, _ = _register_doctor(client, "ldd@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    client.post(
        "/api/v1/appointments",
        json={"title": "Follow-up", "doctor_id": doc["id"], "scheduled_at": _future(1)},
        headers={"Authorization": f"Bearer {pat_token}"},
    )

    resp = client.get("/api/v1/appointments", headers={"Authorization": f"Bearer {doc_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_get_appointment_detail(client: TestClient):
    pat_token, _ = _register_patient(client, "gpat@test.com")
    doc_token, _ = _register_doctor(client, "gdoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    create_resp = client.post(
        "/api/v1/appointments",
        json={"title": "Detail", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    appt_id = create_resp.json()["id"]

    resp = client.get(
        f"/api/v1/appointments/{appt_id}",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == appt_id
    assert data["doctor_name"] is not None
    assert "audit_logs" in data


def test_update_appointment(client: TestClient):
    pat_token, _ = _register_patient(client, "upat@test.com")
    doc_token, _ = _register_doctor(client, "udoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Old", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    resp = client.patch(
        f"/api/v1/appointments/{appt['id']}",
        json={"title": "Updated"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


# ─── Cancel ─────────────────────────────────────────────


def test_cancel_appointment(client: TestClient):
    pat_token, _ = _register_patient(client, "cpat@test.com")
    doc_token, _ = _register_doctor(client, "cdoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Cancel Me", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    resp = client.post(
        f"/api/v1/appointments/{appt['id']}/cancel",
        json={"reason": "Not feeling well"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "cancelled"
    assert data["cancellation_reason"] == "Not feeling well"


def test_cancel_already_cancelled_raises_422(client: TestClient):
    pat_token, _ = _register_patient(client, "ccpat@test.com")
    doc_token, _ = _register_doctor(client, "ccdoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Double Cancel", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    client.post(
        f"/api/v1/appointments/{appt['id']}/cancel",
        json={"reason": "First"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )

    resp = client.post(
        f"/api/v1/appointments/{appt['id']}/cancel",
        json={"reason": "Second"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 422


# ─── Reschedule ─────────────────────────────────────────


def test_reschedule_appointment(client: TestClient):
    pat_token, _ = _register_patient(client, "rpat@test.com")
    doc_token, _ = _register_doctor(client, "rdoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Reschedule Me", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    new_time = _future(5)
    resp = client.post(
        f"/api/v1/appointments/{appt['id']}/reschedule",
        json={"scheduled_at": new_time, "reason": "Conflict"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "scheduled"


def test_reschedule_cancelled_raises_422(client: TestClient):
    pat_token, _ = _register_patient(client, "rcpat@test.com")
    doc_token, _ = _register_doctor(client, "rcdoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Cancel Then Reschedule", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    client.post(
        f"/api/v1/appointments/{appt['id']}/cancel",
        json={"reason": "Sick"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )

    resp = client.post(
        f"/api/v1/appointments/{appt['id']}/reschedule",
        json={"scheduled_at": _future(5), "reason": "Better now"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 422


# ─── Confirm & Complete ─────────────────────────────────


def test_confirm_appointment(client: TestClient):
    pat_token, _ = _register_patient(client, "cfpat@test.com")
    doc_token, _ = _register_doctor(client, "cfdoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Confirm Me", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    resp = client.post(
        f"/api/v1/appointments/{appt['id']}/confirm",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


def test_complete_appointment(client: TestClient):
    pat_token, _ = _register_patient(client, "copat@test.com")
    doc_token, _ = _register_doctor(client, "codoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Complete Me", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    client.post(
        f"/api/v1/appointments/{appt['id']}/confirm",
        headers={"Authorization": f"Bearer {pat_token}"},
    )

    resp = client.post(
        f"/api/v1/appointments/{appt['id']}/complete?follow_up_notes=All+good",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["follow_up_notes"] == "All good"


def test_patient_cannot_complete_appointment(client: TestClient):
    pat_token, _ = _register_patient(client, "pcnopat@test.com")
    doc_token, _ = _register_doctor(client, "pcnodoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "No Complete", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    resp = client.post(
        f"/api/v1/appointments/{appt['id']}/complete",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 403


# ─── Conflict Detection ────────────────────────────────


def test_conflict_detection_rejects_overlap(client: TestClient):
    pat_token, _ = _register_patient(client, "cfpat1@test.com")
    doc_token, _ = _register_doctor(client, "cfdoc1@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    future_time = _future(3)
    client.post(
        "/api/v1/appointments",
        json={"title": "First", "doctor_id": doc["id"], "scheduled_at": future_time},
        headers={"Authorization": f"Bearer {pat_token}"},
    )

    resp = client.post(
        "/api/v1/appointments",
        json={"title": "Second (Conflict)", "doctor_id": doc["id"], "scheduled_at": future_time},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 409


# ─── Recurring ──────────────────────────────────────────


def test_create_recurring_daily(client: TestClient):
    pat_token, _ = _register_patient(client, "rdpat@test.com")
    doc_token, _ = _register_doctor(client, "rddoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    resp = client.post(
        "/api/v1/appointments/recurring",
        json={
            "doctor_id": doc["id"],
            "scheduled_at": _future(1),
            "title": "Daily Check",
            "frequency": "daily",
            "max_occurrences": 3,
        },
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Daily Check"


# ─── Availability ───────────────────────────────────────


def test_set_and_get_availability(client: TestClient, db_session: Session):
    doc_token, _ = _register_doctor(client, "avdoc@test.com")
    doc = _get_user(client, doc_token)

    slots = [
        {"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
        {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"},
    ]
    resp = client.post(
        "/api/v1/appointments/doctor/slots",
        json=slots,
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    get_resp = client.get(
        "/api/v1/appointments/doctor/slots",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert len(get_resp.json()) == 2


def test_get_available_slots(client: TestClient, db_session: Session):
    doc_token, _ = _register_doctor(client, "asdoc@test.com")
    doc = _get_user(client, doc_token)

    client.post(
        "/api/v1/appointments/doctor/slots",
        json=[{"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"}],
        headers={"Authorization": f"Bearer {doc_token}"},
    )

    from datetime import date, timezone
    next_monday = date.today()
    while next_monday.weekday() != 0:
        next_monday += timedelta(days=1)

    resp = client.get(
        f"/api/v1/appointments/doctor/available-slots?doctor_id={doc['id']}&date={next_monday.isoformat()}",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert resp.status_code == 200
    slots = resp.json()
    assert len(slots) > 0
    assert "start" in slots[0]
    assert "end" in slots[0]


# ─── Audit Log ──────────────────────────────────────────


def test_audit_log_created_on_create(client: TestClient):
    pat_token, _ = _register_patient(client, "alpat@test.com")
    doc_token, _ = _register_doctor(client, "aldoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Audit Test", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    resp = client.get(
        f"/api/v1/appointments/{appt['id']}/audit",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200
    logs = resp.json()
    assert any(log["action"] == "created" for log in logs)


def test_audit_log_has_cancel_and_reschedule(client: TestClient):
    pat_token, _ = _register_patient(client, "alcp@test.com")
    doc_token, _ = _register_doctor(client, "alcd@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Full Audit", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    client.post(
        f"/api/v1/appointments/{appt['id']}/cancel",
        json={"reason": "Testing"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )

    resp = client.get(
        f"/api/v1/appointments/{appt['id']}/audit",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    actions = [log["action"] for log in resp.json()]
    assert "created" in actions
    assert "cancelled" in actions


# ─── Reminder ───────────────────────────────────────────


def test_send_reminder(client: TestClient):
    pat_token, _ = _register_patient(client, "rmpat@test.com")
    doc_token, _ = _register_doctor(client, "rmdoc@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Remind Me", "doctor_id": doc["id"], "scheduled_at": _future(3)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    resp = client.get(
        f"/api/v1/appointments/{appt['id']}/remind",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Reminder sent"


# ─── Role Permissions ──────────────────────────────────


def test_patient_cannot_access_doctor_only_endpoints(client: TestClient):
    pat_token, _ = _register_patient(client, "rbpat@test.com")
    resp = client.post(
        "/api/v1/appointments/doctor/slots",
        json=[],
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 403


def test_unauthorized_access_returns_401(client: TestClient):
    resp = client.get("/api/v1/appointments")
    assert resp.status_code == 401


# ─── IDOR Protection ───────────────────────────────────


def test_patient_cannot_update_others_appointment(client: TestClient):
    pat_a_token, _ = _register_patient(client, "pa@test.com")
    pat_b_token, _ = _register_patient(client, "pb@test.com")
    doc_token, _ = _register_doctor(client, "idord1@test.com")
    pat_a = _get_user(client, pat_a_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "A's", "doctor_id": doc["id"], "scheduled_at": _future(5)},
        headers={"Authorization": f"Bearer {pat_a_token}"},
    ).json()

    resp = client.patch(
        f"/api/v1/appointments/{appt['id']}",
        json={"title": "Hacked"},
        headers={"Authorization": f"Bearer {pat_b_token}"},
    )
    assert resp.status_code == 403


def test_patient_cannot_delete_others_appointment(client: TestClient):
    pat_a_token, _ = _register_patient(client, "pa2@test.com")
    pat_b_token, _ = _register_patient(client, "pb2@test.com")
    doc_token, _ = _register_doctor(client, "idord2@test.com")
    pat_a = _get_user(client, pat_a_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "A's", "doctor_id": doc["id"], "scheduled_at": _future(4)},
        headers={"Authorization": f"Bearer {pat_a_token}"},
    ).json()

    resp = client.delete(
        f"/api/v1/appointments/{appt['id']}",
        headers={"Authorization": f"Bearer {pat_b_token}"},
    )
    assert resp.status_code == 403


def test_doctor_cannot_update_others_appointment(client: TestClient):
    pat_token, _ = _register_patient(client, "p3@test.com")
    doc_a_token, _ = _register_doctor(client, "da@test.com")
    doc_b_token, _ = _register_doctor(client, "db@test.com")
    pat = _get_user(client, pat_token)
    doc_a = _get_user(client, doc_a_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Doc A", "doctor_id": doc_a["id"], "scheduled_at": _future(6)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    resp = client.patch(
        f"/api/v1/appointments/{appt['id']}",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {doc_b_token}"},
    )
    assert resp.status_code == 403


def test_owner_patient_can_update_own_appointment(client: TestClient):
    pat_token, _ = _register_patient(client, "op@test.com")
    doc_token, _ = _register_doctor(client, "od@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Mine", "doctor_id": doc["id"], "scheduled_at": _future(2)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    resp = client.patch(
        f"/api/v1/appointments/{appt['id']}",
        json={"title": "Updated Mine"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Mine"


def test_owner_doctor_can_delete_assigned_appointment(client: TestClient):
    pat_token, _ = _register_patient(client, "dp@test.com")
    doc_token, _ = _register_doctor(client, "dd@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    appt = client.post(
        "/api/v1/appointments",
        json={"title": "Delete Me", "doctor_id": doc["id"], "scheduled_at": _future(2)},
        headers={"Authorization": f"Bearer {pat_token}"},
    ).json()

    resp = client.delete(
        f"/api/v1/appointments/{appt['id']}",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert resp.status_code == 200


# ─── Pagination & Filtering ─────────────────────────────


def test_list_pagination(client: TestClient):
    pat_token, _ = _register_patient(client, "pp@test.com")
    doc_token, _ = _register_doctor(client, "pd@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    resp = client.get(
        "/api/v1/appointments?page=1&per_page=5",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["per_page"] == 5
    assert "total_pages" in data


def test_filter_by_status(client: TestClient):
    pat_token, _ = _register_patient(client, "fs@test.com")
    doc_token, _ = _register_doctor(client, "fd@test.com")
    pat = _get_user(client, pat_token)
    doc = _get_user(client, doc_token)

    resp = client.get(
        "/api/v1/appointments?status=scheduled",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 200


def test_invalid_page_returns_422(client: TestClient):
    pat_token, _ = _register_patient(client, "ip@test.com")
    resp = client.get(
        "/api/v1/appointments?page=0",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 422


def test_invalid_per_page_returns_422(client: TestClient):
    pat_token, _ = _register_patient(client, "ipp@test.com")
    resp = client.get(
        "/api/v1/appointments?per_page=200",
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 422
