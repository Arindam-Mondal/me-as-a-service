/* Client for POST /api/leads. Mirrors streamChat.ts's API-base + credentials pattern.
   Backend contract: 201 {ok:true, id} on success; non-2xx on failure. */

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export type LeadInput = { name: string; email: string; message?: string };
export type LeadResult = { ok: true; id: number };

/** POST a lead. Resolves on success; throws on any non-2xx response or network error. */
export async function postLead(input: LeadInput): Promise<LeadResult> {
  const res = await fetch(`${API_BASE}/api/leads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error(`lead request failed: ${res.status}`);
  }
  return (await res.json()) as LeadResult;
}
