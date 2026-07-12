"""Chat endpoint — grounded answers streamed over SSE (TECHNICAL_SPEC.md §8.1).

Synchronous by design: the Voyage, Supabase, and Anthropic SDKs are used
synchronously, and ``client.messages.stream()`` is a sync context manager. FastAPI
runs the sync generator in its threadpool.
"""

from __future__ import annotations

import uuid
from typing import Iterator

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import settings
from app.deps import get_anthropic, get_embedder
from app.models import ChatRequest
from app.services.answer import stream_answer
from app.services.rate_limit import check_and_consume
from app.services.retrieval import hybrid_search
from app.sse import sse_event
from app.supabase_client import get_client

router = APIRouter()

# Session cookie lifetime (foundation for the rate-limiting slice).
_SID_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

_RATE_LIMIT_MESSAGE = (
    "You've reached the question limit for now. Please try again later — "
    "or use the connect option to reach Arindam directly."
)


def _plant_sid(response: Response, sid: str) -> None:
    """Set the session cookie. httpOnly always; SameSite/Secure env-driven (cross-site prod)."""
    response.set_cookie(
        "sid",
        sid,
        max_age=_SID_MAX_AGE,
        httponly=True,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
        secure=settings.cookie_secure,
    )


def _event_stream(question: str) -> Iterator[str]:
    """Run retrieval + grounded streaming, emitting SSE frames.

    Retrieval/embedding happen up front (a brief pause), then answer tokens
    stream. Any failure is surfaced as an ``error`` event rather than a broken
    connection.
    """
    try:
        chunks = hybrid_search(
            question,
            embedder=get_embedder(),
            client=get_client(),
            settings=settings,
        )
        for delta in stream_answer(
            question,
            chunks,
            client=get_anthropic(),
            model=settings.chat_model,
        ):
            yield sse_event("token", {"text": delta})
        yield sse_event("done", {})
    except Exception:  # noqa: BLE001 — surface a generic error to the client
        yield sse_event("error", {"message": "Something went wrong. Please try again."})


@router.post("/api/chat")
def chat(req: ChatRequest, request: Request) -> Response:
    sid = request.cookies.get("sid") or str(uuid.uuid4())

    # Enforce the caps BEFORE any provider call. Fail open: a limiter hiccup must
    # not 500 the endpoint (a real Supabase outage fails retrieval downstream anyway).
    try:
        limit = check_and_consume(get_client(), sid, settings)
    except Exception:  # noqa: BLE001
        limit = None
    if limit is not None and not limit.allowed:
        response: Response = JSONResponse(
            status_code=429,
            content={
                "error": "rate_limited",
                "limit": limit.limit,
                "message": _RATE_LIMIT_MESSAGE,
                "reset_at": limit.reset_at,
            },
        )
        _plant_sid(response, sid)
        return response

    response = StreamingResponse(
        _event_stream(req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable proxy buffering (nginx/render)
        },
    )
    _plant_sid(response, sid)
    return response
