"""Unit tests for the rate limiter (no network — a fake Supabase client)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.rate_limit import check_and_consume, next_utc_midnight


class FakeClient:
    """Records rpc calls and returns a canned payload."""

    def __init__(self, data):
        self._data = data
        self.calls: list[tuple[str, dict]] = []

    def rpc(self, name, params):
        self.calls.append((name, params))
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=self._data))


def _settings(enabled=True, session=10, daily=100):
    return SimpleNamespace(
        rate_limit_enabled=enabled,
        session_question_limit=session,
        daily_question_limit=daily,
    )


def test_disabled_allows_without_touching_the_db():
    client = FakeClient(data=None)
    result = check_and_consume(client, "sid-1", _settings(enabled=False))
    assert result.allowed is True
    assert result.limit is None
    assert client.calls == []  # no rpc when disabled


def test_allowed_calls_rpc_with_env_limits():
    client = FakeClient(data=[{"allowed": True, "limit_hit": None}])
    result = check_and_consume(client, "sid-1", _settings(session=7, daily=42))
    assert result.allowed is True
    assert result.limit is None
    assert result.reset_at is None
    assert client.calls == [
        (
            "check_rate_limit",
            {"p_session_key": "sid-1", "p_session_limit": 7, "p_daily_limit": 42},
        )
    ]


def test_blocked_session_returns_limit_and_reset():
    client = FakeClient(data=[{"allowed": False, "limit_hit": "session"}])
    result = check_and_consume(client, "sid-1", _settings())
    assert result.allowed is False
    assert result.limit == "session"
    assert result.reset_at == next_utc_midnight()


def test_blocked_daily_returns_limit_and_reset():
    client = FakeClient(data=[{"allowed": False, "limit_hit": "daily"}])
    result = check_and_consume(client, "sid-1", _settings())
    assert result.allowed is False
    assert result.limit == "daily"
    assert result.reset_at is not None


def test_next_utc_midnight_is_tomorrow_at_zero():
    now = datetime(2026, 7, 12, 15, 30, 0, tzinfo=timezone.utc)
    assert next_utc_midnight(now) == "2026-07-13T00:00:00+00:00"
