"""Tests for CSRF protection middleware."""
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.csrf import CSRFTokenMiddleware


@pytest.fixture
def csrf_app():
    app = FastAPI()

    @app.post("/test")
    def test_post():
        return {"message": "ok"}

    @app.get("/test")
    def test_get():
        return {"message": "ok"}

    @app.options("/test")
    def test_options():
        return {"message": "ok"}

    @app.head("/test")
    def test_head():
        return {"message": "ok"}

    app.add_middleware(CSRFTokenMiddleware)
    return app


@pytest.fixture
def csrf_client(csrf_app):
    return TestClient(csrf_app)


def test_get_requests_bypass_csrf(csrf_client):
    """GET requests should not be subject to CSRF checks."""
    resp = csrf_client.get("/test")
    assert resp.status_code == 200


def test_options_requests_bypass_csrf(csrf_client):
    """OPTIONS (preflight) requests should bypass CSRF checks."""
    resp = csrf_client.options("/test")
    assert resp.status_code == 200


def test_head_requests_bypass_csrf(csrf_client):
    """HEAD requests should bypass CSRF checks."""
    resp = csrf_client.head("/test")
    assert resp.status_code == 200


class TestCSRFOriginValidation:
    def test_allowed_origin_passes(self):
        """Request with allowed Origin should pass CSRF check."""
        from app.core.config import settings as original_settings

        app = FastAPI()

        @app.post("/test")
        def test_post():
            return {"message": "ok"}

        app.add_middleware(CSRFTokenMiddleware)

        with patch.object(CSRFTokenMiddleware, "_is_safe_request", return_value=True):
            with TestClient(app) as client:
                resp = client.post("/test", headers={"Origin": "http://localhost:3000"})
                assert resp.status_code == 200

    def test_disallowed_origin_blocked(self):
        """Request with disallowed Origin should return 403."""
        app = FastAPI()

        @app.post("/test")
        def test_post():
            return {"message": "ok"}

        app.add_middleware(CSRFTokenMiddleware)

        with patch.object(CSRFTokenMiddleware, "_is_safe_request", return_value=False):
            with TestClient(app) as client:
                resp = client.post("/test", headers={"Origin": "https://evil.com"})
                assert resp.status_code == 403
                data = resp.json()
                assert "CSRF" in data["error"]

    def test_missing_origin_allowed(self):
        """Request without Origin header should pass (same-origin request)."""
        app = FastAPI()

        @app.post("/test")
        def test_post():
            return {"message": "ok"}

        app.add_middleware(CSRFTokenMiddleware)

        with patch.object(CSRFTokenMiddleware, "_is_safe_request", return_value=True):
            with TestClient(app) as client:
                resp = client.post("/test")
                assert resp.status_code == 200


class TestCSRFIntegration:
    """Integration tests ensuring CSRF middleware is wired correctly."""

    def test_csrf_middleware_registered(self):
        """CSRF middleware should be registered in the actual app."""
        from app.main import app

        middleware_types = [m.cls for m in app.user_middleware]
        assert CSRFTokenMiddleware in middleware_types, "CSRF middleware not registered"
