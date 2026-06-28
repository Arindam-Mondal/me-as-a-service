"""Voyage AI embedding wrapper (TECHNICAL_SPEC.md §1, §9).

voyage-3 produces 1024-dim vectors. Voyage distinguishes between embedding
documents (the corpus) and queries via ``input_type`` for better retrieval.
"""

from __future__ import annotations

import voyageai


class Embedder:
    def __init__(self, api_key: str, model: str = "voyage-3") -> None:
        self._client = voyageai.Client(api_key=api_key)
        self._model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        result = self._client.embed(texts, model=self._model, input_type="document")
        return result.embeddings

    def embed_query(self, text: str) -> list[float]:
        result = self._client.embed([text], model=self._model, input_type="query")
        return result.embeddings[0]
