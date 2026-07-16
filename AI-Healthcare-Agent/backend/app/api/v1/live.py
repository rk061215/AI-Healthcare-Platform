"""Kubernetes liveness probe — shallow check that the process is alive."""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/live")
def liveness_probe():
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
