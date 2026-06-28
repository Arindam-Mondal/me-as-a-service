"""Ingest content/*.md into Supabase (TECHNICAL_SPEC.md §9).

Pipeline: read markdown -> chunk -> Voyage embed -> replace rows per source file.
Run from the backend/ directory:  python scripts/ingest.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the `app` package importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.pgvector import to_pgvector  # noqa: E402
from app.services.chunking import chunk_markdown  # noqa: E402
from app.services.embedder import Embedder  # noqa: E402
from app.supabase_client import get_client  # noqa: E402

# repo_root/content  (ingest.py is at backend/scripts/ingest.py -> parents[2] == repo root)
CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


def main() -> int:
    md_files = sorted(CONTENT_DIR.glob("*.md"))
    if not md_files:
        print(f"No markdown files found in {CONTENT_DIR}")
        return 1

    embedder = Embedder(settings.voyage_api_key, settings.embedding_model)
    client = get_client()

    total_chunks = 0
    for md_path in md_files:
        source_file = md_path.name
        text = md_path.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, source_file=source_file)
        if not chunks:
            print(f"  {source_file}: no chunks, skipping")
            continue

        embeddings = embedder.embed_documents([c.content for c in chunks])

        rows = [
            {
                "source_file": source_file,
                "title": c.title,
                "content": c.content,
                "metadata": c.metadata,
                "embedding": to_pgvector(emb),
            }
            for c, emb in zip(chunks, embeddings)
        ]

        # Replace existing rows for this file so re-ingest is idempotent.
        client.table("documents").delete().eq("source_file", source_file).execute()
        client.table("documents").insert(rows).execute()

        total_chunks += len(rows)
        print(f"  {source_file}: {len(rows)} chunks ingested")

    print(f"Done. {len(md_files)} file(s), {total_chunks} chunk(s) total.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
