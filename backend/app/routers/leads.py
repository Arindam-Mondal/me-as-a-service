"""Lead capture endpoint — POST /api/leads (TECHNICAL_SPEC.md §8.2).

Stores the lead in Supabase (source of truth), then emails the owner in a background
task. The email is best-effort: it runs after the response is sent, so SMTP latency or
failure never blocks or fails the visitor's submit.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models import LeadRequest
from app.services.leads import persist_lead
from app.services.notifier import get_notifier
from app.supabase_client import get_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/leads")
def create_lead(req: LeadRequest, background_tasks: BackgroundTasks) -> JSONResponse:
    try:
        lead_id = persist_lead(get_client(), req)
    except Exception:  # noqa: BLE001 — the DB row is the source of truth; tell the visitor to retry
        logger.exception("Failed to persist lead")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "Could not save your details. Please try again."},
        )

    background_tasks.add_task(
        get_notifier().notify,
        lead_id=lead_id,
        name=req.name,
        email=req.email,
        message=req.message,
    )
    return JSONResponse(status_code=201, content={"ok": True, "id": lead_id})
