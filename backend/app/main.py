"""FastAPI application entry point.

Run locally:  uv run uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import chat, health, leads
from app.version import API_VERSION

app = FastAPI(title="Me-as-a-Service API", version=API_VERSION)

# Cookies require explicit origins + credentials (a wildcard "*" is disallowed
# alongside allow_credentials).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_origin_regex=settings.allowed_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(leads.router)
