import { describe, it, expect, vi, afterEach } from "vitest";
import { postLead } from "./postLead";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => vi.restoreAllMocks());

describe("postLead", () => {
  it("POSTs the lead as JSON and resolves with {ok, id}", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ ok: true, id: 12 }, 201));

    const result = await postLead({ name: "Jane", email: "jane@x.com", message: "hi" });

    expect(result).toEqual({ ok: true, id: 12 });
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toMatch(/\/api\/leads$/);
    expect(init?.method).toBe("POST");
    expect(JSON.parse(init?.body as string)).toEqual({
      name: "Jane",
      email: "jane@x.com",
      message: "hi",
    });
  });

  it("throws on a non-2xx response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ ok: false }, 500));
    await expect(postLead({ name: "Jane", email: "jane@x.com" })).rejects.toThrow(/500/);
  });
});
