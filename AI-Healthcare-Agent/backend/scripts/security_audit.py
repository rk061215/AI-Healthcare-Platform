"""
Security audit script for AI Healthcare platform.
Usage: python scripts/security_audit.py
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CHECKS = [
    ('JWT_SECRET_KEY is set', lambda: os.environ.get('JWT_SECRET_KEY') not in [None, '', 'test-secret-key']),
    ('CORS_ORIGINS is configured', lambda: os.environ.get('CORS_ORIGINS') not in [None, '']),
    ('SENTRY_DSN is not exposed in code', lambda: check_no_hardcoded_sentry()),
    ('No hardcoded secrets in Python files', lambda: check_no_secrets_in_code()),
    ('Database URL uses non-default user', lambda: os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres').split('://')[1].split(':')[0] not in ['postgres', 'root']),
    ('CSRF protection is enabled', lambda: check_csrf_protection()),
    ('Rate limiting is configured', lambda: 'RATE_LIMIT_ENABLED' in os.environ or check_rate_limit_in_code()),
    ('HTTPS is enforced in production', lambda: check_https_enforcement()),
    ('File upload size is limited', lambda: check_upload_limit()),
    ('Security headers are configured', lambda: check_security_headers()),
]

BACKEND_DIR = Path(__file__).resolve().parent.parent


def get_python_files():
    files = []
    for root, dirs, fnames in os.walk(str(BACKEND_DIR / 'app')):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'venv', 'env')]
        for f in fnames:
            if f.endswith('.py'):
                files.append(os.path.join(root, f))
    return files


def check_no_hardcoded_sentry():
    for fp in get_python_files():
        with open(fp, 'r') as f:
            content = f.read()
            if 'sentry_sdk.init' in content and 'https://' in content:
                return False
    return True


def check_no_secrets_in_code():
    secret_patterns = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api_key\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']',
    ]
    for fp in get_python_files():
        with open(fp, 'r') as f:
            for i, line in enumerate(f.readlines(), 1):
                line_stripped = line.strip()
                if line_stripped.startswith('#') or 'test' in fp:
                    continue
                for pattern in secret_patterns:
                    if re.search(pattern, line_stripped, re.IGNORECASE):
                        if 'os.environ' in line_stripped or 'config.' in line_stripped:
                            continue
                        return False
    return True


def check_csrf_protection():
    csrf_file = BACKEND_DIR / 'app' / 'middleware' / 'csrf.py'
    if csrf_file.exists():
        with open(str(csrf_file), 'r') as f:
            content = f.read()
            return 'origin' in content.lower() and 'CSRFTokenMiddleware' in content
    return False


def check_rate_limit_in_code():
    rl_file = BACKEND_DIR / 'app' / 'middleware' / 'rate_limit.py'
    if rl_file.exists():
        with open(str(rl_file), 'r') as f:
            return 'rate' in f.read().lower()
    return False


def check_https_enforcement():
    main_py = BACKEND_DIR / 'app' / 'main.py'
    if main_py.exists():
        with open(str(main_py), 'r') as f:
            content = f.read()
            return 'https' in content.lower() or 'strict-transport' in content.lower()
    return False


def check_upload_limit():
    config_py = BACKEND_DIR / 'app' / 'core' / 'config.py'
    if config_py.exists():
        with open(str(config_py), 'r') as f:
            content = f.read()
            return 'max' in content.lower() and ('upload' in content.lower() or 'size' in content.lower())
    return False


def check_security_headers():
    sec_file = BACKEND_DIR / 'app' / 'middleware' / 'security.py'
    if sec_file.exists():
        with open(str(sec_file), 'r') as f:
            content = f.read()
            return 'x-content-type-options' in content.lower()
    return False


def run_audit():
    results = []
    for name, check_fn in CHECKS:
        try:
            passed = check_fn()
        except Exception as e:
            passed = False
            print(f'  Error checking "{name}": {e}')
        results.append((name, passed))

    print(f'\n{"="*60}')
    print(f'  Security Audit Report')
    print(f'{"="*60}\n')

    passed_count = 0
    for name, passed in results:
        status = 'PASS' if passed else 'FAIL'
        if passed:
            passed_count += 1
        print(f'  [{status}]  {name}')

    print(f'\n{"="*60}')
    print(f'  {passed_count}/{len(results)} checks passed')
    print(f'{"="*60}\n')

    return passed_count == len(results)


if __name__ == '__main__':
    success = run_audit()
    sys.exit(0 if success else 1)
