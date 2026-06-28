"""Markdown chunking — pure functions, no I/O (TECHNICAL_SPEC.md §9).

Splits a markdown document into one chunk per heading section. The heading text
is kept as the chunk `title` and is also prepended to the chunk `content` so it
contributes to both the embedding and the full-text index. Sections that contain
only a heading (no body) are dropped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


@dataclass
class Chunk:
    title: Optional[str]
    content: str
    metadata: dict


def chunk_markdown(markdown: str, *, source_file: str = "") -> list[Chunk]:
    """Split markdown into heading-delimited chunks.

    A new chunk begins at each ATX heading (``#`` .. ``######``). Body text
    before the first heading becomes a chunk with ``title=None``. Sections with
    no body (heading only) are dropped.
    """
    chunks: list[Chunk] = []
    current_title: Optional[str] = None
    current_body: list[str] = []

    def flush() -> None:
        body_text = "\n".join(current_body).strip()
        if not body_text:
            return
        content = f"{current_title}\n{body_text}" if current_title else body_text
        chunks.append(
            Chunk(
                title=current_title,
                content=content,
                metadata={"source_file": source_file, "heading": current_title},
            )
        )

    for line in markdown.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            flush()
            current_title = match.group(2).strip()
            current_body = []
        else:
            current_body.append(line)

    flush()
    return chunks
