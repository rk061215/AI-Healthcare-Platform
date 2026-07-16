"""Tests for rate limiting middleware."""
from fastapi.testclient import TestClient

from tests.conftest import PATIENT_PASSWORD


def test_login_rate_limit(client: TestClient):
    """Login endpoint should return 429 after exceeding rate limit."""
    # Register a patient first
    client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "ratelimit@patient.com",
            "password": PATIENT_PASSWORD,
            "confirm_password": PATIENT_PASSWORD,
            "full_name": "Rate Limit Patient",
            "terms_accepted": True,
        },
    )

    # Attempt login more times than the limit (default: 5/min)
    status_codes = []
    for _ in range(10):
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "ratelimit@patient.com",
                "password": PATIENT_PASSWORD,
                "role": "patient",
            },
        )
        status_codes.append(resp.status_code)

    # At least some requests should be rate limited
    limited = [s for s in status_codes if s == 429]
    assert len(limited) > 0, f"Expected at least one 429, got status codes: {status_codes}"


def test_register_rate_limit(client: TestClient):
    """Registration endpoint should be rate limited under global limit."""
    # Quick-fire registrations with different emails
    status_codes = []
    for i in range(80):
        resp = client.post(
            "/api/v1/auth/register/patient",
            json={
                "email": f"ratelimit{i}@patient.com",
                "password": PATIENT_PASSWORD,
                "confirm_password": PATIENT_PASSWORD,
                "full_name": f"Rate Limit {i}",
                "terms_accepted": True,
            },
        )
        status_codes.append(resp.status_code)
        if resp.status_code == 429:
            break

    # Should eventually get rate limited
    limited = [s for s in status_codes if s == 429]
    assert len(limited) > 0, "Expected global rate limit to kick in"
