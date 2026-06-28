"""Query the agent from the CLI (TECHNICAL_SPEC.md §5, §6).

Runs the full RAG loop: embed query -> hybrid_search RPC -> grounded Claude answer.
Run from the backend/ directory:

    python scripts/query.py "What are Arindam's skills?"
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the `app` package importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anthropic import Anthropic  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.answer import answer  # noqa: E402
from app.services.embedder import Embedder  # noqa: E402
from app.services.retrieval import hybrid_search  # noqa: E402
from app.supabase_client import get_client  # noqa: E402


def main() -> int:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('Usage: python scripts/query.py "your question"')
        return 1

    embedder = Embedder(settings.voyage_api_key, settings.embedding_model)
    client = get_client()
    anthropic = Anthropic(api_key=settings.anthropic_api_key)

    chunks = hybrid_search(question, embedder=embedder, client=client, settings=settings)
    reply = answer(question, chunks, client=anthropic, model=settings.chat_model)

    print(f"\nQ: {question}\n")
    print(f"A: {reply}\n")

    # Debug aid for learning: show which chunks were retrieved.
    if chunks:
        labels = ", ".join(
            f"{c.get('title') or c.get('source_file')} ({c.get('score'):.4f})"
            for c in chunks
        )
        print(f"[retrieved: {labels}]")
    else:
        print("[retrieved: none — decline path]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
