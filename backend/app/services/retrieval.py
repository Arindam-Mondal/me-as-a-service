"""Hybrid retrieval: vector + full-text fused with RRF (TECHNICAL_SPEC.md §5).

The fusion itself runs inside Postgres via the ``hybrid_search`` RPC. This module
embeds the query, calls the RPC, and returns scored chunks. A simple relevance
gate (empty result -> no context) lets the answer layer take the decline path.
"""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.pgvector import to_pgvector
from app.services.embedder import Embedder


def hybrid_search(
    query: str,
    *,
    embedder: Embedder,
    client: Any,
    settings: Settings,
) -> list[dict]:
    """Return up to ``retrieval_top_k`` fused chunks, highest score first."""
    query_embedding = embedder.embed_query(query)
    response = client.rpc(
        "hybrid_search",
        {
            "query_text": query,
            "query_embedding": to_pgvector(query_embedding),
            "match_count": settings.retrieval_top_k,
            "rrf_k": settings.rrf_k,
            "candidate_count": settings.retrieval_top_n,
        },
    ).execute()
    return response.data or []
