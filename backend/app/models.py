"""Pydantic request/response models for the HTTP API (TECHNICAL_SPEC.md §8)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Cap history so a crafted client can't POST an oversized payload.
    history: list[Message] = Field(default_factory=list, max_length=20)
