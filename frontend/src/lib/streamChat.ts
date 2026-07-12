/* SSE client for POST /api/chat. EventSource can't POST, so we read the fetch
   ReadableStream and parse SSE frames by hand. Backend contract: token {text} /
   done {} / error {message}; sets an httpOnly `sid` cookie (credentials: include). */

export type ChatRole = "user" | "assistant";
export type HistoryMsg = { role: ChatRole; content: string };

export type ChatEvent =
  | { event: "token"; data: { text: string } }
  | { event: "done"; data: Record<string, never> }
  | { event: "error"; data: { message: string } }
  | { event: string; data: unknown };

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

/** Async generator yielding parsed SSE events from the chat endpoint. */
export async function* streamChat(
  message: string,
  history: HistoryMsg[],
  signal: AbortSignal,
): AsyncGenerator<ChatEvent> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
    credentials: "include",
    signal,
  });

  if (res.status === 429) {
    yield { event: "limit", data: {} };
    return;
  }
  if (!res.ok || !res.body) {
    throw new Error(`chat request failed: ${res.status}`);
  }

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += value;
    const frames = buf.split("\n\n");
    buf = frames.pop() ?? ""; // keep trailing partial frame
    for (const frame of frames) {
      const parsed = parseFrame(frame);
      if (parsed) yield parsed;
    }
  }
  const tail = parseFrame(buf);
  if (tail) yield tail;
}

function parseFrame(frame: string): ChatEvent | null {
  const trimmed = frame.trim();
  if (!trimmed) return null;
  let event = "message";
  let data: unknown = {};
  for (const line of trimmed.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) {
      const raw = line.slice(5).trim();
      try {
        data = JSON.parse(raw);
      } catch {
        data = { text: raw };
      }
    }
  }
  return { event, data } as ChatEvent;
}
