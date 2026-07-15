"""Lead persistence — the durable record for a captured lead (TECHNICAL_SPEC.md §4.2).

This is the source of truth: the row is inserted before any notification is attempted,
so a notifier failure can never lose a lead.
"""

from __future__ import annotations

from typing import Any

from app.models import LeadRequest


def persist_lead(client: Any, lead: LeadRequest) -> int:
    """Insert a lead via the Supabase client (service role) and return its new id."""
    row = {
        "name": lead.name,
        "email": lead.email,
        "message": lead.message,
        "conversation_context": [m.model_dump() for m in lead.conversation_context],
    }
    response = client.table("leads").insert(row).execute()
    return response.data[0]["id"]
