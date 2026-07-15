"""Pydantic request/response models for the HTTP API (TECHNICAL_SPEC.md §8)."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Cap history so a crafted client can't POST an oversized payload.
    history: list[Message] = Field(default_factory=list, max_length=20)


# Matches the frontend's client-side check (ConnectForm.tsx) so validation is consistent.
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class LeadRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(max_length=254)
    message: str | None = Field(default=None, max_length=2000)
    # Optional chat transcript for context (agentic capture fills this later).
    conversation_context: list[Message] = Field(default_factory=list, max_length=40)

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    @field_validator("email")
    @classmethod
    def _email_shape(cls, v: str) -> str:
        v = v.strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("invalid email")
        return v
