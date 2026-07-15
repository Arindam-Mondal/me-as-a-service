"""HTTP layer tests — POST /api/leads (Supabase + notifier mocked)."""

from __future__ import annotations

import app.routers.leads as leads_module
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class _RecordingNotifier:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def notify(self, **kwargs) -> None:
        self.calls.append(kwargs)


def _stub_persist(monkeypatch, *, lead_id: int = 42, capture: list | None = None):
    def fake_persist(client, lead):
        if capture is not None:
            capture.append(lead)
        return lead_id

    monkeypatch.setattr(leads_module, "get_client", lambda: object())
    monkeypatch.setattr(leads_module, "persist_lead", fake_persist)


def test_create_lead_returns_201_with_id(monkeypatch):
    _stub_persist(monkeypatch, lead_id=7)
    monkeypatch.setattr(leads_module, "get_notifier", lambda: _RecordingNotifier())

    r = client.post("/api/leads", json={"name": "Jane Doe", "email": "jane@example.com"})

    assert r.status_code == 201
    assert r.json() == {"ok": True, "id": 7}


def test_create_lead_persists_parsed_fields_and_notifies(monkeypatch):
    captured: list = []
    notifier = _RecordingNotifier()
    _stub_persist(monkeypatch, lead_id=99, capture=captured)
    monkeypatch.setattr(leads_module, "get_notifier", lambda: notifier)

    r = client.post(
        "/api/leads",
        json={"name": "  Bob  ", "email": "bob@example.com", "message": "Hi there"},
    )

    assert r.status_code == 201
    # persisted lead has trimmed name + parsed fields
    assert captured[0].name == "Bob"
    assert captured[0].email == "bob@example.com"
    assert captured[0].message == "Hi there"
    # notifier scheduled as a background task and run after the response
    assert notifier.calls == [
        {"lead_id": 99, "name": "Bob", "email": "bob@example.com", "message": "Hi there"}
    ]


def test_create_lead_rejects_bad_email(monkeypatch):
    _stub_persist(monkeypatch)
    monkeypatch.setattr(leads_module, "get_notifier", lambda: _RecordingNotifier())

    r = client.post("/api/leads", json={"name": "Jane", "email": "not-an-email"})
    assert r.status_code == 422


def test_create_lead_rejects_missing_name(monkeypatch):
    _stub_persist(monkeypatch)
    monkeypatch.setattr(leads_module, "get_notifier", lambda: _RecordingNotifier())

    r = client.post("/api/leads", json={"name": "   ", "email": "jane@example.com"})
    assert r.status_code == 422


def test_create_lead_500_when_persist_fails(monkeypatch):
    def boom(client, lead):
        raise RuntimeError("db down")

    monkeypatch.setattr(leads_module, "get_client", lambda: object())
    monkeypatch.setattr(leads_module, "persist_lead", boom)
    monkeypatch.setattr(leads_module, "get_notifier", lambda: _RecordingNotifier())

    r = client.post("/api/leads", json={"name": "Jane", "email": "jane@example.com"})
    assert r.status_code == 500
    assert r.json()["ok"] is False
