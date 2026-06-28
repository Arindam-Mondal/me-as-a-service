"""Helper for passing embeddings to Postgres / PostgREST.

PostgREST does not reliably bind a JSON number array to a pgvector column, so we
serialize embeddings to the bracketed string form (e.g. '[0.1,0.2,...]') that
pgvector parses. Used for both inserts and the hybrid_search RPC.
"""

from typing import Sequence


def to_pgvector(embedding: Sequence[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"
