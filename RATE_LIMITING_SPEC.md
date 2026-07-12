# RATE_LIMITING_SPEC.md — Guardrails design (Phase 6)

> Focused design doc for the abuse/cost guardrails on the public chat. Pairs with
> [`TECHNICAL_SPEC.md`](./TECHNICAL_SPEC.md) §7 (which sketched the original counter) and
> [`CLAUDE.md`](./CLAUDE.md) Phase 6. **Status:** designed, not yet implemented.
> **Date:** 2026-07-12.

## 1. Context & problem

`POST /api/chat` calls paid providers (Voyage embeddings + Anthropic generation) on every
request, and the endpoint is public with no authentication. Today there is **no ceiling on
spend** — a script hitting the endpoint in a loop can run up the owner's API bill without
limit. At ~$0.008 per worst-case request (Haiku, 1,024 output tokens), 10,000 scripted
requests ≈ **$80 in a single run**. Before the site is shared widely, we need a bounded,
low-friction cost guardrail.

## 2. Goals / non-goals

**Goals**
- Put a **hard ceiling on daily provider spend**, regardless of traffic or intent.
- Give casual repeat-visitors a fair per-visitor allowance without accounts.
- Zero added infrastructure — reuse the existing Supabase database and `sid` cookie.
- Keep the request path synchronous and simple (matches the rest of the backend).

**Non-goals (explicitly deferred)**
- Bulletproof abuse resistance (per-IP limits, CAPTCHA/Turnstile, bot fingerprinting).
- Content moderation of visitor input.
- Authenticated/quota'd API access.

These were considered and dropped for a personal-portfolio threat model (see §8).

## 3. Design decisions (agreed)

| Decision | Choice | Why |
|---|---|---|
| Protection level | **Basic / cost-first** | Portfolio threat model is accidental overuse + the odd scripted burst, not a determined adversary. The global cap bounds the bill; heavier defenses add friction/complexity for little gain. |
| Identity | **`sid` httpOnly cookie** (already issued) | No accounts, no PII, already wired as the rate-limit foundation. |
| Windows | **Both per-session and global reset daily (UTC)** | A returning recruiter gets a fresh allowance tomorrow; "lifetime per cookie" would permanently block legit repeat visitors. Cost is bounded by the global cap either way. |
| Defaults | **10 / session / day**, **100 / day global** | Global cap sets the spend ceiling: `100 × max_tokens(1024)` on Haiku ≈ **$0.80/day worst case**. Both env-configurable. |
| Enforcement point | **Before any provider call** | A 429 must cost nothing. |
| Counting | **Increment on accept (reserve a slot), before streaming** | Guarantees the cap holds even if generation errors mid-stream — the safe direction for a cost guardrail. Trade-off: a request that errors still consumes one slot (acceptable). |
| Storage | **Supabase Postgres table + atomic upsert RPC** | Durable across Render restarts/redeploys (in-memory would reset the daily counter on every cold start, leaking the ceiling). Already in the stack. |

## 4. Data model — `supabase/migrations/0002_rate_limits.sql`

```sql
create table rate_limits (
  key         text not null,                                   -- sid, or 'global'
  kind        text not null,                                   -- 'session' | 'global'
  window_date date not null default (now() at time zone 'utc')::date,
  count       int  not null default 0,
  updated_at  timestamptz not null default now(),
  primary key (key, kind, window_date)
);

-- Atomic increment; returns the new count in one round trip (race-free).
create or replace function bump_rate_limit(p_key text, p_kind text)
returns int language plpgsql as $$
declare v_count int;
begin
  insert into rate_limits (key, kind, count)
  values (p_key, p_kind, 1)
  on conflict (key, kind, window_date)
  do update set count = rate_limits.count + 1, updated_at = now()
  returning count into v_count;
  return v_count;
end $$;
```
RLS: service-role only (backend never exposes this table to the browser).

## 5. Enforcement — `backend/app/services/rate_limit.py`, wired into `routers/chat.py`

Before retrieval/generation, inside `POST /api/chat`:
1. Resolve `sid` (existing cookie logic).
2. **Read** today's `session` count (key=`sid`) and `global` count in one query.
3. `session ≥ SESSION_QUESTION_LIMIT` → **429** `{limit:"session"}`.
   `global ≥ DAILY_QUESTION_LIMIT` → **429** `{limit:"daily", reset_at:<next UTC midnight>}`.
   Returned as JSON **before** the SSE stream opens (no provider spend).
4. Otherwise **increment both** via `bump_rate_limit` (reserve the slot), then run the
   existing `hybrid_search` → `stream_answer` path.

The read-then-increment race is acceptable at this scale (single Render instance, low
traffic); worst case is a slight over-count under concurrency, never a cost breach because
the global cap still gates every request.

## 6. Config — `backend/app/config.py`
```
SESSION_QUESTION_LIMIT = 10     # per sid per UTC day
DAILY_QUESTION_LIMIT   = 100    # global per UTC day  → hard cost ceiling
```
Both env-overridable (project convention). `.env.example` updated. Lowering
`DAILY_QUESTION_LIMIT` is the single knob that sets maximum daily spend.

## 7. API / UX contract
- **429** body: `{ "error":"rate_limited", "limit":"session|daily", "message":"…", "reset_at":"<iso8601|null>" }`.
- Frontend already turns any 429 into the `LimitNotice` ("out of ink") component and keeps
  the Connect option — **no required frontend change.** Optional enhancement: add
  `session_remaining` to the SSE `done` event to later show "3 questions left today."
- **Request-size guard:** cap `ChatRequest.history` (≤ 20 messages, each ≤ 4,000 chars) so a
  crafted client can't POST an oversized payload; `message` is already capped at 2,000.

## 8. Cost analysis (why 10/100)

Haiku 4.5 = $1/1M input, $5/1M output. Per worst-case request ≈ 2,500 input + 1,024 output ≈
**$0.008**. With the global cap:

| Scenario | $/day | $5 credit lasts |
|---|---|---|
| Sustained abuse, cap maxed daily, max-length answers | ~$0.80 | **~6 days** |
| Cap maxed daily, typical answer length | ~$0.30 | ~16 days |
| Realistic traffic (~20 q/day) | ~$0.06 | ~80 days |

Without the cap this is **unbounded**. The global daily limit is what converts "$5 could
vanish in an afternoon" into "$5 survives ~a week under sustained attack."

## 9. Testing (mocked providers, no network)
- Boundary: `limit-1` passes, `limit` blocks — for both session and global.
- Daily reset: a row dated yesterday doesn't count toward today.
- 429 short-circuits **before** provider calls (assert embedder/Anthropic not invoked).
- Request-size guard rejects oversized `history`.

## 10. Extensibility (how this grows)
- **Per-IP tier:** add an `ip` counter keyed on `X-Forwarded-For` (+ `allow_origin_regex`
  already present) for stronger abuse resistance — the table/RPC generalize as-is.
- **Bot challenge:** gate the first request behind Cloudflare Turnstile; verify server-side
  before the rate-limit check.
- **Sliding window / token-bucket:** swap the daily-window counter for a Redis token bucket
  if sub-day granularity is ever needed.
- **Per-visitor quotas with accounts:** if auth is added, key the session counter on user id
  instead of the cookie.
```
