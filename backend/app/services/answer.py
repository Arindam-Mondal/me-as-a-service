"""Grounded answer generation with Claude (TECHNICAL_SPEC.md §6).

The system prompt restricts the model to the retrieved context. When there is no
context, we short-circuit to a polite decline + connect offer rather than calling
the model (avoids a wasted, potentially ungrounded generation). The `capture_lead`
tool is added in a later slice.
"""

from __future__ import annotations

from typing import Any, Iterator

OWNER_NAME = "Arindam"

SYSTEM_PROMPT = f"""You are the personal AI assistant for {OWNER_NAME}. You answer \
questions about {OWNER_NAME} on his behalf for visitors to his website.

Strict rules:
- Answer ONLY using the information inside the <context> block. The context is the \
only source of truth about {OWNER_NAME}.
- If the answer is not in the context, do NOT guess or use outside knowledge. Say \
politely that you don't have that information, and offer to connect the visitor with \
{OWNER_NAME} directly (they can use the "connect" option to leave their name and email).
- Be warm, concise, and professional. Speak about {OWNER_NAME} in the third person.
- Never invent facts, dates, employers, or links that are not in the context."""

DECLINE_MESSAGE = (
    f"I don't have that information in what {OWNER_NAME} has shared with me. "
    f"If you'd like, I can help you connect with {OWNER_NAME} directly — just share "
    f"your name and email and he'll follow up."
)


def _format_context(chunks: list[dict]) -> str:
    blocks = []
    for c in chunks:
        label = c.get("title") or c.get("source_file") or "section"
        blocks.append(f"[{label}]\n{c.get('content', '')}")
    return "\n\n".join(blocks)


def _user_content(question: str, chunks: list[dict]) -> str:
    return (
        f"<context>\n{_format_context(chunks)}\n</context>\n\n"
        f"Visitor question: {question}"
    )


def answer(
    question: str,
    chunks: list[dict],
    *,
    client: Any,
    model: str,
    max_tokens: int = 1024,
) -> str:
    """Generate a grounded answer, or a decline message when there is no context."""
    if not chunks:
        return DECLINE_MESSAGE

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _user_content(question, chunks)}],
    )
    return "".join(block.text for block in message.content if block.type == "text")


def stream_answer(
    question: str,
    chunks: list[dict],
    *,
    client: Any,
    model: str,
    max_tokens: int = 1024,
) -> Iterator[str]:
    """Yield the grounded answer as text deltas, or the decline message when there
    is no context. Mirrors ``answer()`` but streams via the Anthropic SDK."""
    if not chunks:
        yield DECLINE_MESSAGE
        return

    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _user_content(question, chunks)}],
    ) as stream:
        for text in stream.text_stream:
            yield text
