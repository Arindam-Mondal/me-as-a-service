"""Health check (TECHNICAL_SPEC.md §8.5)."""

from __future__ import annotations

from fastapi import APIRouter

from app.version import API_VERSION

router = APIRouter()


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": API_VERSION}
