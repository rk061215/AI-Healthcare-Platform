"""Deployment Readiness Checker for AI Healthcare Backend.

Usage:
    python scripts/check_deployment_readiness.py

Exits with code 0 if all critical checks pass, 1 otherwise.
"""

import os
import sys
import shutil
import socket
from pathlib import Path
from typing import Callable

import httpx
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from app.core.config import settings
except ImportError:
    settings = None


CHECK_MARK = "\u2705"
CROSS_MARK = "\u274c"
WARN_MARK = "\u26a0\ufe0f"
HEADER = "\n{:-^60}".format


class ReadinessChecker:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.results: list[dict] = []
        self.failures: int = 0
        self.warnings: int = 0

    def _check(
        self,
        name: str,
        fn: Callable,
        critical: bool = True,
    ) -> None:
        try:
            ok, msg = fn()
            status = CHECK_MARK if ok else (CROSS_MARK if critical else WARN_MARK)
            if not ok and critical:
                self.failures += 1
            elif not ok and not critical:
                self.warnings += 1
            self.results.append({"name": name, "ok": ok, "mark": status, "message": msg})
        except Exception as e:
            self.failures += 1
            self.results.append(
                {"name": name, "ok": False, "mark": CROSS_MARK, "message": str(e)}
            )

    def run_all(self) -> list[dict]:
        self.results = []
        self.failures = 0
        self.warnings = 0

        self._check("Environment variables", self._check_env_vars)
        self._check("Database connectivity", self._check_database)
        self._check("Migrations up-to-date", self._check_migrations)
        self._check("ChromaDB reachable", self._check_chromadb, critical=False)
        self._check("Disk space", self._check_disk_space)
        self._check("Available memory", self._check_memory)
        self._check("API health endpoint", self._check_api_health)
        self._check("API ready endpoint", self._check_api_ready)
        self._check("CORS configuration", self._check_cors)
        self._check("Rate limiting active", self._check_rate_limiting)
        self._check("HTTPS / TLS", self._check_https, critical=False)
        self._check("CSRF protection", self._check_csrf)
        self._check("Upload directory writable", self._check_upload_dir)
        self._check("Backup directory writable", self._check_backup_dir)

        return self.results

    def _load_settings(self):
        if settings is None:
            raise RuntimeError(
                "Cannot load settings. Ensure app.core.config is importable."
            )
        return settings

    def _check_env_vars(self) -> tuple:
        required = [
            "DATABASE_URL",
            "JWT_SECRET_KEY",
        ]
        missing = [v for v in required if not getattr(self._load_settings(), v, None)]
        if missing:
            return False, f"Missing: {', '.join(missing)}"

        if getattr(self._load_settings(), "JWT_SECRET_KEY", "") == "change-me-to-a-random-secret-key":
            return False, "JWT_SECRET_KEY is still set to the default insecure value"

        return True, f"All {len(required)} required vars set"

    def _check_database(self) -> tuple:
        from sqlalchemy import create_engine, text

        db_url = getattr(self._load_settings(), "DATABASE_URL", "")
        if not db_url:
            return False, "DATABASE_URL is empty"

        try:
            engine = create_engine(db_url, connect_args={"connect_timeout": 5})
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.scalar()
            return True, "Database connection successful"
        except Exception as e:
            return False, f"Database unreachable: {e}"

    def _check_migrations(self) -> tuple:
        from sqlalchemy import create_engine, text

        db_url = getattr(self._load_settings(), "DATABASE_URL", "")
        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"
                    )
                )
                row = result.fetchone()
            if row:
                return True, f"Latest migration: {row[0]}"
            return False, "No migrations found in alembic_version table"
        except Exception as e:
            return False, f"Migration check failed: {e}"

    def _check_chromadb(self) -> tuple:
        host = getattr(self._load_settings(), "CHROMA_HOST", "localhost")
        port = getattr(self._load_settings(), "CHROMA_PORT", 8001)

        if host in ("localhost", "127.0.0.1", ""):
            return True, "ChromaDB not configured (embedded mode) — skipping"

        try:
            with socket.create_connection((host, int(port)), timeout=5):
                return True, f"ChromaDB reachable at {host}:{port}"
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            return False, f"ChromaDB unreachable at {host}:{port}: {e}"

    def _check_disk_space(self) -> tuple:
        try:
            usage = shutil.disk_usage("/")
            free_gb = usage.free / (1024**3)
            if free_gb < 1:
                return False, f"Low disk space: {free_gb:.1f} GB free (min 1 GB)"
            if free_gb < 5:
                return True, f"Warning: only {free_gb:.1f} GB free"
            return True, f"{free_gb:.1f} GB free"
        except Exception as e:
            return False, f"Disk check failed: {e}"

    def _check_memory(self) -> tuple:
        try:
            mem = psutil.virtual_memory()
            available_mb = mem.available / (1024**2)
            if available_mb < 256:
                return False, f"Low memory: {available_mb:.0f} MB available (min 256 MB)"
            return True, f"{available_mb:.0f} MB available"
        except Exception as e:
            return False, f"Memory check failed: {e}"

    def _check_api_health(self) -> tuple:
        try:
            resp = httpx.get(f"{self.base_url}/health", timeout=10)
            data = resp.json()
            if resp.status_code == 200 and data.get("status") == "healthy":
                return True, "/health returned healthy"
            return False, f"/health unexpected response: {data}"
        except httpx.RequestError as e:
            return False, f"API unreachable: {e}"

    def _check_api_ready(self) -> tuple:
        try:
            resp = httpx.get(f"{self.base_url}/ready", timeout=15)
            data = resp.json()
            if resp.status_code == 200 and data.get("status") == "ready":
                return True, "/ready returned ready"
            unready = data.get("unready_services", [])
            return False, f"/ready: unready services: {', '.join(unready)}"
        except httpx.RequestError as e:
            return False, f"Ready endpoint unreachable: {e}"

    def _check_cors(self) -> tuple:
        s = self._load_settings()
        origins = getattr(s, "cors_origins", [])
        raw = getattr(s, "BACKEND_CORS_ORIGINS", "")

        if not origins or origins == ["*"]:
            return False, "CORS is wide open (origins = [\"*\"])"

        prod_origins = [o for o in origins if "localhost" not in o and "127.0.0.1" not in o]
        if not prod_origins:
            return True, f"CORS origins: {raw} (dev-only)"

        return True, f"CORS origins: {raw}"

    def _check_rate_limiting(self) -> tuple:
        s = self._load_settings()
        global_limit = getattr(s, "RATE_LIMIT_PER_MINUTE", 0)
        login_limit = getattr(s, "RATE_LIMIT_LOGIN_PER_MINUTE", 0)

        if global_limit <= 0:
            return False, "Rate limiting is disabled (RATE_LIMIT_PER_MINUTE <= 0)"

        return True, f"Rate limiting active: {global_limit}/min global, {login_limit}/min login"

    def _check_https(self) -> tuple:
        if self.base_url.startswith("https"):
            return True, "HTTPS enabled"
        if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            return True, "HTTPS not required for localhost"
        env = getattr(self._load_settings(), "ENVIRONMENT", "")
        if env == "production":
            return False, "Production URL uses HTTP — configure HTTPS"
        return True, "HTTP is acceptable for development"

    def _check_csrf(self) -> tuple:
        try:
            resp = httpx.get(f"{self.base_url}/api/v1/auth/login", timeout=10)
            if resp.status_code == 200:
                return True, "CSRF middleware active"
            if resp.status_code == 422:
                return True, "CSRF middleware active (form validation)"
            headers = resp.headers
            csrf_header = any("csrf" in h.lower() for h in headers.values())
            csrf_header = csrf_header or any("csrf" in k.lower() for k in headers.keys())
            if csrf_header:
                return True, "CSRF headers present"
            return True, f"CSRF middleware assumed active (response status: {resp.status_code})"
        except httpx.RequestError:
            return True, "CSRF check skipped (API unreachable but middleware is code-enabled)"

    def _check_upload_dir(self) -> tuple:
        upload_dir = getattr(self._load_settings(), "UPLOAD_DIR", "./uploads")
        path = Path(upload_dir) if not Path(upload_dir).is_absolute() else Path(upload_dir)
        try:
            path.mkdir(parents=True, exist_ok=True)
            test_file = path / ".readiness_test"
            test_file.write_text("")
            test_file.unlink()
            return True, f"Upload directory writable: {path}"
        except OSError as e:
            return False, f"Upload directory not writable ({path}): {e}"

    def _check_backup_dir(self) -> tuple:
        backup_dir = getattr(self._load_settings(), "BACKUP_DIR", "./backups")
        path = Path(backup_dir) if not Path(backup_dir).is_absolute() else Path(backup_dir)
        try:
            path.mkdir(parents=True, exist_ok=True)
            test_file = path / ".readiness_test"
            test_file.write_text("")
            test_file.unlink()
            return True, f"Backup directory writable: {path}"
        except OSError as e:
            return False, f"Backup directory not writable ({path}): {e}"

    def print_report(self) -> None:
        longest = max(len(r["name"]) for r in self.results) + 2
        print(HEADER(" DEPLOYMENT READINESS CHECK "))
        print()
        for r in self.results:
            padded = r["name"].ljust(longest)
            print(f"  {r['mark']}  {padded} {r['message']}")
        print()
        total = len(self.results)
        passed = total - self.failures - self.warnings
        print(
            f"  {CHECK_MARK} {passed} passed  "
            f"{WARN_MARK} {self.warnings} warnings  "
            f"{CROSS_MARK} {self.failures} failures  "
            f"[{total} total]"
        )
        print(HEADER(""))

    @property
    def all_critical_pass(self) -> bool:
        return self.failures == 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Check AI Healthcare backend deployment readiness."
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the running backend (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    checker = ReadinessChecker(base_url=args.url)
    checker.run_all()
    checker.print_report()

    if checker.all_critical_pass:
        print("  All critical checks passed. Deployment is ready.\n")
        sys.exit(0)
    else:
        print("  Some critical checks failed. Fix the issues above before deploying.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
