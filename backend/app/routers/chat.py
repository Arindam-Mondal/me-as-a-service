"""Chat endpoint — grounded answers streamed over SSE (TECHNICAL_SPEC.md §8.1).

Synchronous by design: the Voyage, Supabase, and Anthropic SDKs are used
synchronously, and ``client.messages.stream()`` is a sync context manager. FastAPI
runs the sync generator in its threadpool.
"""

from __future__ import annotations

import uuid
from typing import Iterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.config import settings
from app.deps import get_anthropic, get_embedder
from app.models import ChatRequest
from app.services.answer import stream_answer
from app.services.retrieval import hybrid_search
from app.sse import sse_event
from app.supabase_client import get_client

router = APIRouter()

# Session cookie lifetime (foundation for the rate-limiting slice).
_SID_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


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
def chat(req: ChatRequest, request: Request) -> StreamingResponse:
    sid = request.cookies.get("sid") or str(uuid.uuid4())

    response = StreamingResponse(
        _event_stream(req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable proxy buffering (nginx/render)
        },
    )
    # httpOnly + SameSite=Lax for local dev. Cross-site (Vercel <-> Render) will
    # need SameSite=None; Secure — handled in the deploy slice.
    response.set_cookie(
        "sid",
        sid,
        max_age=_SID_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return response
