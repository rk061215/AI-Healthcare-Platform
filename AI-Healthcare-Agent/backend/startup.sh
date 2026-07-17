#!/bin/sh
set -e

echo "=== AI Healthcare Backend Startup ==="

echo "[1/4] Running database migrations..."
alembic upgrade head
echo "[1/4] Migrations complete."

echo "[2/4] Checking Tesseract OCR..."
if command -v tesseract >/dev/null 2>&1; then
    echo "  tesseract: $(tesseract --version 2>&1 | head -1)"
    echo "  languages: $(tesseract --list-langs 2>&1 | tail -n +2 | tr '\n' ' ')"
else
    echo "  WARNING: tesseract not found"
fi

echo "[3/4] Checking system dependencies..."
if command -v pdftotext >/dev/null 2>&1; then
    echo "  poppler-utils: available"
else
    echo "  WARNING: poppler-utils not found"
fi

echo "[4/4] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
