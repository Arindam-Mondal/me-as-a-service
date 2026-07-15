"""Owner notifications for captured leads.

Fulfils the PRD's planned ``Notifier`` interface (FR4.4). The v1 concrete sink is
**email via Gmail SMTP** — the DB write is the persistence step (``services/leads.py``),
so this layer only pings the owner. The ABC keeps callers decoupled so a Slack/other
notifier can be added later without changing the router.

Everything here is best-effort and **fail-open**: a missing credential or an SMTP
error is logged and swallowed, never raised into the request path (the lead is already
stored by the time we notify).
"""

from __future__ import annotations

import logging
import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587  # STARTTLS


class Notifier(ABC):
    @abstractmethod
    def notify(self, *, lead_id: int, name: str, email: str, message: str | None) -> None:
        """Notify the owner about a new lead. Must not raise on delivery failure."""


class NullNotifier(Notifier):
    """No-op sink used when email credentials are absent (local dev / CI)."""

    def notify(self, *, lead_id: int, name: str, email: str, message: str | None) -> None:
        logger.info("Lead #%s stored; email notification disabled (no credentials).", lead_id)


class EmailNotifier(Notifier):
    """Sends a plaintext email to the owner via Gmail SMTP + STARTTLS."""

    def __init__(self, sender: str, app_password: str, recipient: str) -> None:
        self._sender = sender
        self._app_password = app_password
        self._recipient = recipient

    def notify(self, *, lead_id: int, name: str, email: str, message: str | None) -> None:
        msg = EmailMessage()
        msg["Subject"] = f"New lead: {name}"
        msg["From"] = self._sender
        msg["To"] = self._recipient
        msg["Reply-To"] = email
        msg.set_content(
            f"New lead from the me-as-a-service site.\n\n"
            f"Name:    {name}\n"
            f"Email:   {email}\n"
            f"Message: {message or '(none)'}\n\n"
            f"Lead id: {lead_id}\n"
        )
        try:
            with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(self._sender, self._app_password)
                smtp.send_message(msg)
        except Exception:  # noqa: BLE001 — fail-open; lead is already persisted
            logger.exception("Failed to send lead email for lead #%s", lead_id)


def get_notifier() -> Notifier:
    """Return an ``EmailNotifier`` if Gmail creds are configured, else a ``NullNotifier``."""
    recipient = settings.lead_notify_recipient
    if settings.gmail_address and settings.gmail_app_password and recipient:
        return EmailNotifier(settings.gmail_address, settings.gmail_app_password, recipient)
    return NullNotifier()
