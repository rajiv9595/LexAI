"""LexAssist prototype API application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import assistant, auth, documents, health, history, research
from app.core.config import settings

app = FastAPI(
    title="LexAssist API",
    description="Backend API for the LexAssist legal assistance prototype.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/")
def read_root() -> dict[str, str]:
    """Return basic prototype API information."""
    return {
        "name": "LexAssist API",
        "version": "0.1.0",
        "status": "prototype",
    }


app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(assistant.router, prefix=settings.api_prefix)
app.include_router(documents.router, prefix=settings.api_prefix)
app.include_router(research.router, prefix=settings.api_prefix)
app.include_router(history.router, prefix=settings.api_prefix)
