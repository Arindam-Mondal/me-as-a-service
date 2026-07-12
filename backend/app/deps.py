"""Shared, lazily-constructed provider clients for the HTTP layer.

Constructed on first use (not at import) and cached, so importing routers/tests
doesn't spin up network clients. The Supabase client lives in ``supabase_client``.
"""

from __future__ import annotations

from functools import lru_cache

from anthropic import Anthropic

from app.config import settings
from app.services.embedder import Embedder


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    return Embedder(settings.voyage_api_key, settings.embedding_model)


@lru_cache(maxsize=1)
def get_anthropic() -> Anthropic:
    return Anthropic(api_key=settings.anthropic_api_key)
