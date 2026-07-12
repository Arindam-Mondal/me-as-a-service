"""Rate limiting — per-session + global daily caps (RATE_LIMITING_SPEC.md).

Enforcement is a single atomic Postgres RPC (``check_rate_limit``) that reads today's
counts and, only if under both env-driven limits, reserves a slot by incrementing both.
Limits are passed in from config on every call, so changing the env vars changes the
caps with no redeploy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Any


@dataclass
class RateLimitResult:
    allowed: bool
    limit: str | None = None      # "session" | "daily" | None
    reset_at: str | None = None   # ISO-8601 (next UTC midnight) when blocked


def next_utc_midnight(now: datetime | None = None) -> str:
    """ISO-8601 timestamp for the next UTC midnight (when a daily window resets)."""
    now = now or datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).date()
    return datetime.combine(tomorrow, time.min, tzinfo=timezone.utc).isoformat()


def check_and_consume(client: Any, sid: str, settings: Any) -> RateLimitResult:
    """Check both caps and, if under limit, reserve a slot (increment). Atomic in the DB."""
    if not settings.rate_limit_enabled:
        return RateLimitResult(allowed=True)

    response = client.rpc(
        "check_rate_limit",
        {
            "p_session_key": sid,
            "p_session_limit": settings.session_question_limit,
            "p_daily_limit": settings.daily_question_limit,
        },
    ).execute()

    row = (response.data or [{}])[0]
    if row.get("allowed"):
        return RateLimitResult(allowed=True)
    return RateLimitResult(
        allowed=False,
        limit=row.get("limit_hit"),
        reset_at=next_utc_midnight(),
    )
