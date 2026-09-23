"""Health check route."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def read_health() -> dict[str, str]:
    """Return service health for the prototype API."""
    return {"status": "ok", "service": "lexassist-api"}
