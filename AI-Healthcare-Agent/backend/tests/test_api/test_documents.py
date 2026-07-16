import io
import uuid

from fastapi.testclient import TestClient

from tests.conftest import DOCTOR_PASSWORD, PATIENT_PASSWORD


def _register_patient(client: TestClient, email: str) -> tuple[str, dict]:
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
    return data["access_token"], data


def _register_doctor(client: TestClient, email: str) -> tuple[str, dict]:
    resp = client.post(
        "/api/v1/auth/register/doctor",
        json={
            "email": email,
            "password": DOCTOR_PASSWORD,
            "confirm_password": DOCTOR_PASSWORD,
            "full_name": "Test Doctor",
            "specialization": "Cardiology",
            "license_number": "LIC-12345",
            "years_of_experience": 10,
        },
    )
    data = resp.json()
    return data["access_token"], data


def _make_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"


def _make_png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


def _make_jpeg_bytes() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00" * 100


# ─── Upload ────────────────────────────────────────────────


def test_upload_pdf(client: TestClient):
    token, _ = _register_patient(client, "upl-pdf@test.com")
    pdf_bytes = _make_pdf_bytes()
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["file_type"] == "pdf"
    assert data["file_size"] == len(pdf_bytes)
    assert data["status"] == "uploaded"
    assert data["virus_scan_status"] == "clean"
    assert data["version"] == 1
    assert "id" in data
    assert "document_group_id" in data
    assert data["original_filename"] == "test.pdf"


def test_upload_png(client: TestClient):
    token, _ = _register_patient(client, "upl-png@test.com")
    png_bytes = _make_png_bytes()
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("scan.png", io.BytesIO(png_bytes), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["file_type"] == "png"


def test_upload_jpeg(client: TestClient):
    token, _ = _register_patient(client, "upl-jpg@test.com")
    jpg_bytes = _make_jpeg_bytes()
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("photo.jpeg", io.BytesIO(jpg_bytes), "image/jpeg")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["file_type"] == "jpeg"


def test_doctor_upload_for_patient(client: TestClient):
    pat_token, pat_data = _register_patient(client, "doc-upload-pat@test.com")
    doc_token, _ = _register_doctor(client, "doc-upload-doc@test.com")
    pdf_bytes = _make_pdf_bytes()
    resp = client.post(
        "/api/v1/documents/doctor/upload",
        params={"patient_id": pat_data["user"]["id"]},
        files={"file": ("rx.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["file_type"] == "pdf"
    assert data["status"] == "uploaded"


def test_upload_invalid_file_type(client: TestClient):
    token, _ = _register_patient(client, "upl-bad@test.com")
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("doc.txt", io.BytesIO(b"hello"), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422, resp.text


def test_upload_unauthorized(client: TestClient):
    pdf_bytes = _make_pdf_bytes()
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert resp.status_code == 401, resp.text


def test_patient_cannot_use_doctor_endpoint(client: TestClient):
    pat_token, _ = _register_patient(client, "pat-no-doctor@test.com")
    pdf_bytes = _make_pdf_bytes()
    resp = client.post(
        "/api/v1/documents/doctor/upload",
        params={"patient_id": str(uuid.uuid4())},
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    assert resp.status_code == 403, resp.text


# ─── List ──────────────────────────────────────────────────


def test_list_documents_empty(client: TestClient):
    token, _ = _register_patient(client, "list-empty@test.com")
    resp = client.get(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_documents_with_data(client: TestClient):
    token, _ = _register_patient(client, "list-data@test.com")
    for i in range(3):
        data = f"content-{i}-{uuid.uuid4()}".encode()
        client.post(
            "/api/v1/documents/upload",
            files={"file": (f"doc{i}.pdf", io.BytesIO(data), "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
    resp = client.get(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 3


def test_list_documents_pagination(client: TestClient):
    token, _ = _register_patient(client, "list-page@test.com")
    for i in range(5):
        data = f"content-{i}-{uuid.uuid4()}".encode()
        client.post(
            "/api/v1/documents/upload",
            files={"file": (f"doc{i}.pdf", io.BytesIO(data), "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
    resp = client.get(
        "/api/v1/documents",
        params={"page": 1, "per_page": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["total_pages"] == 3


def test_list_documents_filter_by_type(client: TestClient):
    token, _ = _register_patient(client, "list-filter@test.com")
    pdf_bytes = _make_pdf_bytes()
    png_bytes = _make_png_bytes()
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("img.png", io.BytesIO(png_bytes), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.get(
        "/api/v1/documents",
        params={"file_type": "png"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 1
    assert all(d["file_type"] == "png" for d in data["items"])


# ─── Get Detail ────────────────────────────────────────────


def test_get_document_detail(client: TestClient):
    token, _ = _register_patient(client, "detail@test.com")
    pdf_bytes = _make_pdf_bytes()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    doc_id = upload_resp.json()["id"]
    resp = client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"] == doc_id
    assert data["file_type"] == "pdf"
    assert data["original_filename"] == "test.pdf"


def test_get_document_wrong_patient_returns_404(client: TestClient):
    token_a, _ = _register_patient(client, "wrong-pat-a@test.com")
    token_b, _ = _register_patient(client, "wrong-pat-b@test.com")
    pdf_bytes = _make_pdf_bytes()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    doc_id = upload_resp.json()["id"]
    resp = client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404, resp.text


# ─── Download ──────────────────────────────────────────────


def test_download_document(client: TestClient):
    token, _ = _register_patient(client, "dl@test.com")
    pdf_bytes = _make_pdf_bytes()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    doc_id = upload_resp.json()["id"]
    resp = client.get(
        f"/api/v1/documents/{doc_id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.content == pdf_bytes
    assert "Content-Disposition" in resp.headers


# ─── Versions ──────────────────────────────────────────────


def test_get_versions(client: TestClient):
    token, _ = _register_patient(client, "vers@test.com")
    pdf_bytes = _make_pdf_bytes()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("v1.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    group_id = upload_resp.json()["document_group_id"]
    doc_id = upload_resp.json()["id"]
    resp = client.get(
        f"/api/v1/documents/{doc_id}/versions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    versions = resp.json()
    assert len(versions) == 1
    assert versions[0]["version"] == 1


def test_versioning_with_explicit_group_id(client: TestClient):
    token, _ = _register_patient(client, "multi-ver@test.com")
    pdf_bytes = _make_pdf_bytes()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("v1.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    group_id = upload_resp.json()["document_group_id"]

    pdf_bytes2 = b"%PDF-1.4\nModified content\n%%EOF"
    upload_resp2 = client.post(
        "/api/v1/documents/upload",
        params={"document_group_id": group_id},
        files={"file": ("v2.pdf", io.BytesIO(pdf_bytes2), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_resp2.status_code == 200, upload_resp2.text
    assert upload_resp2.json()["version"] == 2

    doc_id = upload_resp2.json()["id"]
    resp = client.get(
        f"/api/v1/documents/{doc_id}/versions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    versions = resp.json()
    assert len(versions) == 2
    assert versions[0]["version"] == 1
    assert versions[1]["version"] == 2
    assert versions[1]["is_latest_version"] is True
    assert versions[0]["is_latest_version"] is False


# ─── Delete ────────────────────────────────────────────────


def test_delete_document(client: TestClient):
    token, _ = _register_patient(client, "del@test.com")
    pdf_bytes = _make_pdf_bytes()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    doc_id = upload_resp.json()["id"]
    resp = client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    resp2 = client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 404


# ─── Retry ─────────────────────────────────────────────────


def test_retry_failed_document_not_supported_for_non_failed(client: TestClient):
    token, _ = _register_patient(client, "retry-fail@test.com")
    pdf_bytes = _make_pdf_bytes()
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    doc_id = upload_resp.json()["id"]
    resp = client.post(
        f"/api/v1/documents/{doc_id}/retry",
        files={"file": ("retry.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422, resp.text


# ─── Duplicate Content ─────────────────────────────────────


def test_duplicate_content_rejected(client: TestClient):
    token, _ = _register_patient(client, "dedup@test.com")
    pdf_bytes = _make_pdf_bytes()
    resp1 = client.post(
        "/api/v1/documents/upload",
        files={"file": ("a.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == 200, resp1.text
    resp2 = client.post(
        "/api/v1/documents/upload",
        files={"file": ("b.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 422, resp2.text


# ─── Invalid Pagination ────────────────────────────────────


def test_list_documents_invalid_per_page(client: TestClient):
    token, _ = _register_patient(client, "pag-bad@test.com")
    resp = client.get(
        "/api/v1/documents",
        params={"per_page": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422, resp.text
