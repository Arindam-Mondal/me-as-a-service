"""Notifier tests — EmailNotifier (SMTP mocked) + get_notifier factory."""

from __future__ import annotations

import smtplib

import app.services.notifier as notifier_module
from app.services.notifier import EmailNotifier, NullNotifier, get_notifier


class _FakeSMTP:
    """Records interactions; acts as the smtplib.SMTP context manager."""

    instances: list["_FakeSMTP"] = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.sent = []
        self.logged_in = None
        self.started_tls = False
        _FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, user, password):
        self.logged_in = (user, password)

    def send_message(self, msg):
        self.sent.append(msg)


def test_email_notifier_sends_with_correct_headers(monkeypatch):
    _FakeSMTP.instances.clear()
    monkeypatch.setattr(smtplib, "SMTP", _FakeSMTP)

    EmailNotifier("owner@gmail.com", "app-pass", "owner@gmail.com").notify(
        lead_id=5, name="Jane", email="jane@x.com", message="hello"
    )

    assert len(_FakeSMTP.instances) == 1
    smtp = _FakeSMTP.instances[0]
    assert smtp.started_tls is True
    assert smtp.logged_in == ("owner@gmail.com", "app-pass")
    assert len(smtp.sent) == 1
    msg = smtp.sent[0]
    assert msg["To"] == "owner@gmail.com"
    assert msg["Subject"] == "New lead: Jane"
    assert msg["Reply-To"] == "jane@x.com"
    assert "jane@x.com" in msg.get_content()


def test_email_notifier_swallows_smtp_errors(monkeypatch):
    def boom(*a, **k):
        raise smtplib.SMTPException("smtp down")

    monkeypatch.setattr(smtplib, "SMTP", boom)

    # Must not raise — fail-open (the lead is already stored).
    EmailNotifier("owner@gmail.com", "app-pass", "owner@gmail.com").notify(
        lead_id=5, name="Jane", email="jane@x.com", message=None
    )


def test_get_notifier_returns_email_when_configured(monkeypatch):
    monkeypatch.setattr(notifier_module.settings, "gmail_address", "owner@gmail.com")
    monkeypatch.setattr(notifier_module.settings, "gmail_app_password", "app-pass")
    monkeypatch.setattr(notifier_module.settings, "lead_notify_to", None)

    assert isinstance(get_notifier(), EmailNotifier)


def test_get_notifier_returns_null_when_creds_absent(monkeypatch):
    monkeypatch.setattr(notifier_module.settings, "gmail_address", None)
    monkeypatch.setattr(notifier_module.settings, "gmail_app_password", None)
    monkeypatch.setattr(notifier_module.settings, "lead_notify_to", None)

    assert isinstance(get_notifier(), NullNotifier)
