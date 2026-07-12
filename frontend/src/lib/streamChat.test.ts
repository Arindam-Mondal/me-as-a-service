import { describe, it, expect, vi, afterEach } from "vitest";
import { streamChat } from "./streamChat";

function sseResponse(body: string, status = 200): Response {
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(body));
      controller.close();
    },
  });
  return new Response(stream, { status, headers: { "content-type": "text/event-stream" } });
}

afterEach(() => vi.restoreAllMocks());

describe("streamChat", () => {
  it("parses token frames then done", async () => {
    const body =
      'event: token\ndata: {"text": "Hello"}\n\n' +
      'event: token\ndata: {"text": " there"}\n\n' +
      "event: done\ndata: {}\n\n";
    vi.spyOn(globalThis, "fetch").mockResolvedValue(sseResponse(body));

    const events = [];
    for await (const ev of streamChat("hi", [], new AbortController().signal)) events.push(ev);

    const tokens = events.filter((e) => e.event === "token").map((e) => (e.data as any).text);
    expect(tokens).toEqual(["Hello", " there"]);
    expect(events.at(-1)?.event).toBe("done");
  });

  it("emits a limit event on HTTP 429", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(sseResponse("", 429));
    const events = [];
    for await (const ev of streamChat("hi", [], new AbortController().signal)) events.push(ev);
    expect(events).toEqual([{ event: "limit", data: {} }]);
  });

  it("surfaces error frames", async () => {
    const body = 'event: error\ndata: {"message": "boom"}\n\n';
    vi.spyOn(globalThis, "fetch").mockResolvedValue(sseResponse(body));
    const events = [];
    for await (const ev of streamChat("hi", [], new AbortController().signal)) events.push(ev);
    expect(events[0]).toEqual({ event: "error", data: { message: "boom" } });
  });
});
