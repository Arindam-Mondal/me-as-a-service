"""Server-Sent Events formatting helper (TECHNICAL_SPEC.md §6.4)."""

from __future__ import annotations

import json
from typing import Any


def sse_event(event: str, data: dict[str, Any]) -> str:
    """Format one SSE frame: an event name + a JSON data payload.

    Produces e.g.  ``event: token\\ndata: {"text": "hi"}\\n\\n``.
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
