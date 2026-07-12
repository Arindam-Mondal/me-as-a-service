"""HTTP layer tests — health + /api/chat SSE (providers mocked)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import app.routers.chat as chat_module
from app.main import app

client = TestClient(app)


def _parse_sse(body: str) -> list[tuple[str | None, dict | None]]:
    """Parse a raw SSE body into a list of (event, data) tuples."""
    events: list[tuple[str | None, dict | None]] = []
    for frame in body.strip().split("\n\n"):
        if not frame.strip():
            continue
        event = data = None
        for line in frame.split("\n"):
            if line.startswith("event: "):
                event = line[len("event: ") :]
            elif line.startswith("data: "):
                data = json.loads(line[len("data: ") :])
        events.append((event, data))
    return events


@pytest.fixture(autouse=True)
def _stub_provider_clients(monkeypatch):
    """Provider factories return harmless stubs so nothing hits the network."""
    monkeypatch.setattr(chat_module, "get_embedder", lambda: object())
    monkeypatch.setattr(chat_module, "get_client", lambda: object())
    monkeypatch.setattr(chat_module, "get_anthropic", lambda: object())


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": "0.1.0"}


def test_chat_streams_tokens_then_done(monkeypatch):
    monkeypatch.setattr(
        chat_module, "hybrid_search", lambda q, **kw: [{"title": "Summary", "content": "x"}]
    )
    monkeypatch.setattr(
        chat_module, "stream_answer", lambda q, chunks, **kw: iter(["Hello", " there"])
    )

    r = client.post("/api/chat", json={"message": "hi"})

    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    events = _parse_sse(r.text)
    assert [d["text"] for (e, d) in events if e == "token"] == ["Hello", " there"]
    assert events[-1][0] == "done"
    # session cookie planted (rate-limit foundation)
    assert "sid=" in r.headers.get("set-cookie", "")


def test_chat_decline_when_no_context(monkeypatch):
    # Empty retrieval → real stream_answer yields the decline message, no model call.
    monkeypatch.setattr(chat_module, "hybrid_search", lambda q, **kw: [])

    r = client.post("/api/chat", json={"message": "what is his favorite movie?"})

    assert r.status_code == 200
    events = _parse_sse(r.text)
    joined = "".join(d["text"] for (e, d) in events if e == "token")
    assert "don't have that information" in joined
    assert events[-1][0] == "done"


def test_chat_emits_error_event_on_failure(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("retrieval down")

    monkeypatch.setattr(chat_module, "hybrid_search", boom)

    r = client.post("/api/chat", json={"message": "hi"})

    assert r.status_code == 200
    events = _parse_sse(r.text)
    assert any(e == "error" for (e, _d) in events)


def test_chat_rejects_empty_message():
    r = client.post("/api/chat", json={"message": ""})
    assert r.status_code == 422
