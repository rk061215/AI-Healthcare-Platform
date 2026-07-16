from fastapi.testclient import TestClient

from tests.conftest import DOCTOR_PASSWORD, PATIENT_PASSWORD


# ─── Registration Tests ───────────────────────────────────


def test_register_patient(client: TestClient):
    response = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "new@patient.com",
            "password": PATIENT_PASSWORD,
            "confirm_password": PATIENT_PASSWORD,
            "full_name": "New Patient",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "new@patient.com"
    assert data["user"]["role"] == "patient"
    assert data["expires_in"] == 900


def test_register_patient_missing_terms(client: TestClient):
    response = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "noterms@patient.com",
            "password": PATIENT_PASSWORD,
            "confirm_password": PATIENT_PASSWORD,
            "full_name": "No Terms Patient",
            "terms_accepted": False,
        },
    )
    assert response.status_code == 422


def test_register_patient_password_mismatch(client: TestClient):
    response = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "mismatch@patient.com",
            "password": PATIENT_PASSWORD,
            "confirm_password": "DifferentPass1!",
            "full_name": "Mismatch Patient",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 422


def test_register_patient_weak_password(client: TestClient):
    response = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "weak@patient.com",
            "password": "short",
            "confirm_password": "short",
            "full_name": "Weak Password",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 422


def test_register_duplicate_patient(client: TestClient, patient_token: str):
    response = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "test@patient.com",
            "password": PATIENT_PASSWORD,
            "confirm_password": PATIENT_PASSWORD,
            "full_name": "Test Patient",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["error"].lower()


def test_register_doctor(client: TestClient):
    response = client.post(
        "/api/v1/auth/register/doctor",
        json={
            "email": "dr@test.com",
            "password": DOCTOR_PASSWORD,
            "confirm_password": DOCTOR_PASSWORD,
            "full_name": "Dr. Test",
            "specialization": "Cardiology",
            "license_number": "LIC-98765",
            "hospital_name": "City Hospital",
            "years_of_experience": 15,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["role"] == "doctor"
    assert data["user"]["specialization"] == "Cardiology"
    assert data["user"]["license_number"] == "LIC-98765"
    assert data["user"]["hospital_name"] == "City Hospital"
    assert data["user"]["years_of_experience"] == 15


def test_register_duplicate_doctor(client: TestClient, doctor_token: str):
    response = client.post(
        "/api/v1/auth/register/doctor",
        json={
            "email": "test@doctor.com",
            "password": DOCTOR_PASSWORD,
            "confirm_password": DOCTOR_PASSWORD,
            "full_name": "Test Doctor",
        },
    )
    assert response.status_code == 409


# ─── Login Tests ──────────────────────────────────────────


def test_login_patient(client: TestClient):
    client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "login@patient.com",
            "password": PATIENT_PASSWORD,
            "confirm_password": PATIENT_PASSWORD,
            "full_name": "Login Patient",
            "terms_accepted": True,
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@patient.com", "password": PATIENT_PASSWORD, "role": "patient"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["role"] == "patient"


def test_login_doctor(client: TestClient):
    client.post(
        "/api/v1/auth/register/doctor",
        json={
            "email": "drlogin@test.com",
            "password": DOCTOR_PASSWORD,
            "confirm_password": DOCTOR_PASSWORD,
            "full_name": "Dr. Login",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "drlogin@test.com", "password": DOCTOR_PASSWORD, "role": "doctor"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "doctor"


def test_login_invalid_credentials(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.com", "password": "WrongPass1!", "role": "patient"},
    )
    assert response.status_code == 401


def test_login_wrong_role(client: TestClient):
    client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "wrongrole@test.com",
            "password": PATIENT_PASSWORD,
            "confirm_password": PATIENT_PASSWORD,
            "full_name": "Wrong Role",
            "terms_accepted": True,
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongrole@test.com", "password": PATIENT_PASSWORD, "role": "doctor"},
    )
    assert response.status_code == 401


def test_login_remember_me(client: TestClient):
    client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "remember@patient.com",
            "password": PATIENT_PASSWORD,
            "confirm_password": PATIENT_PASSWORD,
            "full_name": "Remember Me",
            "terms_accepted": True,
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "remember@patient.com",
            "password": PATIENT_PASSWORD,
            "role": "patient",
            "remember_me": True,
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


# ─── Token Refresh Tests ──────────────────────────────────


def test_refresh_token(client: TestClient, patient_refresh_token: str):
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": patient_refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_rotation(client: TestClient, patient_refresh_token: str):
    first = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": patient_refresh_token},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": patient_refresh_token},
    )
    assert second.status_code == 401


def test_refresh_invalid_token(client: TestClient):
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )
    assert response.status_code == 401


# ─── Logout Tests ─────────────────────────────────────────


def test_logout(client: TestClient, patient_refresh_token: str):
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": patient_refresh_token},
    )
    assert response.status_code == 204


def test_logout_revoked_token(client: TestClient, patient_refresh_token: str):
    client.post("/api/v1/auth/logout", json={"refresh_token": patient_refresh_token})
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": patient_refresh_token},
    )
    assert response.status_code == 401


# ─── Me Endpoint Tests ────────────────────────────────────


def test_get_me_patient(client: TestClient, patient_token: str):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@patient.com"
    assert data["role"] == "patient"
    assert data["is_active"] is True


def test_get_me_doctor(client: TestClient, doctor_token: str):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@doctor.com"
    assert data["role"] == "doctor"


def test_get_me_unauthorized(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client: TestClient):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401


# ─── Authorization Tests ──────────────────────────────────


def test_patient_endpoint_rejects_doctor(client: TestClient, doctor_token: str):
    response = client.get(
        "/api/v1/patients/me",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 403


def test_doctor_endpoint_rejects_patient(client: TestClient, patient_token: str):
    response = client.get(
        "/api/v1/doctors/me",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert response.status_code == 403


# ─── Password Validation Tests ────────────────────────────


def test_register_weak_password_no_uppercase(client: TestClient):
    response = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "noupper@test.com",
            "password": "weakpass1!",
            "confirm_password": "weakpass1!",
            "full_name": "No Upper",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 422


def test_register_weak_password_no_special(client: TestClient):
    response = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "nospecial@test.com",
            "password": "WeakPass1",
            "confirm_password": "WeakPass1",
            "full_name": "No Special",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 422
