import io

from fastapi.testclient import TestClient

from tests.conftest import PATIENT_PASSWORD


def _make_png_bytes() -> bytes:
    buf = io.BytesIO()
    from PIL import Image
    img = Image.new("RGB", (200, 150), color="white")
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), "Patient Name: John Doe", fill="black")
    draw.text((10, 60), "Diagnosis: Hypertension", fill="black")
    img.save(buf, format="PNG")
    return buf.getvalue()


def _register_patient(client: TestClient, email: str) -> str:
    resp = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": email,
            "password": PATIENT_PASSWORD,
            "confirm_password": PATIENT_PASSWORD,
            "full_name": "OCR Patient",
            "terms_accepted": True,
        },
    )
    return resp.json()["access_token"]


def test_upload_and_process_report(client: TestClient):
    token = _register_patient(client, "ocr-proc@test.com")
    png_bytes = _make_png_bytes()
    upload_resp = client.post(
        "/api/v1/reports/upload",
        files={"file": ("report.png", io.BytesIO(png_bytes), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_resp.status_code == 200, upload_resp.text
    report_id = upload_resp.json()["id"]

    process_resp = client.post(
        f"/api/v1/reports/{report_id}/process",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert process_resp.status_code == 200, process_resp.text
    data = process_resp.json()
    assert data["status"] == "completed"
    assert data["confidence"] > 0
    assert data["text_length"] > 0
    assert data["provider"] is not None


def test_process_report_returns_text_and_structured_data(client: TestClient):
    token = _register_patient(client, "ocr-structured@test.com")
    png_bytes = _make_png_bytes()
    upload_resp = client.post(
        "/api/v1/reports/upload",
        files={"file": ("doc.png", io.BytesIO(png_bytes), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    report_id = upload_resp.json()["id"]

    client.post(
        f"/api/v1/reports/{report_id}/process",
        headers={"Authorization": f"Bearer {token}"},
    )

    get_resp = client.get(
        f"/api/v1/reports/{report_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200, get_resp.text
    data = get_resp.json()
    assert data["ocr_text"] is not None
    assert data["ocr_text"] != ""
    assert data["ocr_confidence"] is not None
    assert data["ocr_confidence"] > 0
    assert data["ocr_provider"] is not None
    assert data["ocr_pages"] is not None
    assert data["retry_count"] is not None


def test_process_report_twice_returns_completed(client: TestClient):
    token = _register_patient(client, "ocr-twice@test.com")
    png_bytes = _make_png_bytes()
    upload_resp = client.post(
        "/api/v1/reports/upload",
        files={"file": ("rpt.png", io.BytesIO(png_bytes), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    report_id = upload_resp.json()["id"]

    resp1 = client.post(
        f"/api/v1/reports/{report_id}/process",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == 200

    resp2 = client.post(
        f"/api/v1/reports/{report_id}/process",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200


def test_process_nonexistent_report_returns_404(client: TestClient):
    token = _register_patient(client, "ocr-404@test.com")
    resp = client.post(
        "/api/v1/reports/00000000-0000-0000-0000-000000000000/process",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404, resp.text


def test_retry_nonexistent_report_returns_404(client: TestClient):
    token = _register_patient(client, "ocr-retry404@test.com")
    resp = client.post(
        "/api/v1/reports/00000000-0000-0000-0000-000000000000/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404, resp.text


def test_list_reports_shows_ocr_fields(client: TestClient):
    token = _register_patient(client, "ocr-list@test.com")
    png_bytes = _make_png_bytes()
    upload_resp = client.post(
        "/api/v1/reports/upload",
        files={"file": ("r.png", io.BytesIO(png_bytes), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    report_id = upload_resp.json()["id"]

    client.post(
        f"/api/v1/reports/{report_id}/process",
        headers={"Authorization": f"Bearer {token}"},
    )

    list_resp = client.get(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200, list_resp.text
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["ocr_confidence"] is not None
    assert items[0]["ocr_provider"] is not None
    assert items[0]["ocr_pages"] is not None
    assert items[0]["retry_count"] is not None
