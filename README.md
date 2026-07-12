# Me as a Service — an AI twin, grounded in my own words

> A live AI agent that answers questions about me, strictly grounded in documents I've
> written — with hybrid retrieval, token-by-token streaming, cost guardrails, and a
> deliberately hand-made "zine" interface. Built by **[Arindam Mondal](https://linkedin.com/in/amond)**
> as a hobby project to explore agentic AI, RAG, and end-to-end product engineering.

**Ask my AI twin anything** → **[me-as-a-service.vercel.app](https://me-as-a-service.vercel.app/)**  ·  API health → [me-as-a-service.onrender.com/api/health](https://me-as-a-service.onrender.com/api/health)

---

## What this is (30-second version)

Instead of a static "About Me" page, this is a chat interface where a visitor — a recruiter,
a collaborator, a curious stranger — can **ask questions and get grounded answers about my
work, skills, and projects**. The twist that makes it trustworthy: the AI can only answer
from documents I've actually written. Ask something it wasn't told, and it says so and offers
to connect you with me directly, rather than making something up.

It's a working RAG (Retrieval-Augmented Generation) product, small enough to reason about
end-to-end, but built with the same decisions I'd defend in a production system: strict
grounding, hybrid search, streaming, a bounded API bill, a secrets boundary, and tests.

> **Why I built it.** Two reasons. One: I wanted a portfolio piece that *demonstrates* what I
> do (agentic AI, RAG, MCP tooling, full-stack delivery) rather than just claiming it. Two:
> the app itself is a mirror of me — you can learn about me by talking to it, without needing
> my time. This README is the "director's commentary": it walks through *every* significant
> design decision, why I made it, what I traded away, and how I'd extend it.

---

## Architecture at a glance

```
  ┌────────────────────────┐        POST /api/chat (SSE)        ┌──────────────────────────────┐
  │  Frontend (Vercel)     │  ───────────────────────────────▶ │  Backend (Render · Docker)   │
  │  React + Vite + TS     │  ◀───────  token stream  ───────  │  FastAPI (async, SSE)        │
  │  "Zine" neo-brutalist  │                                    │                              │
  │  UI · streaming chat    │                                    │  1. rate-limit check (cost)  │
  └────────────────────────┘                                    │  2. embed query  ─────────▶  │──▶ Voyage AI (embeddings)
                                                                 │  3. hybrid retrieval (RRF)   │──▶ Supabase (pgvector + FTS)
                                                                 │  4. grounded answer, stream  │──▶ Anthropic Claude (Haiku)
                                                                 └──────────────────────────────┘
        Secrets boundary: provider + service-role keys live ONLY on the backend.
        The browser gets a public API base URL and nothing else.
```

**Request lifecycle:** a visitor asks → the backend checks rate limits (before spending a
cent) → embeds the question with Voyage → runs **hybrid search** (semantic + keyword, fused)
against my corpus in Supabase → if nothing relevant is found it declines, otherwise it asks
Claude to answer **using only the retrieved passages** → the answer streams back token by
token over Server-Sent Events.

---

## Tech stack & why each piece

| Layer | Choice | Why this and not the obvious alternative |
|---|---|---|
| **Backend** | Python 3.12 · FastAPI | Async + native SSE streaming; the AI/embeddings ecosystem is Python-first. |
| **LLM** | Anthropic Claude **Haiku 4.5** (default), Opus for escalation | Haiku is fast and cheap ($1/$5 per 1M tok) — the right default for grounded Q&A where the context does the heavy lifting. Model is a config value, not hardcoded. |
| **Embeddings** | Voyage AI `voyage-3` (1024-dim) | Strong retrieval quality; decoupled from the LLM vendor so either can change independently. |
| **Data + search** | Supabase (Postgres) — **pgvector + full-text**, fused with **RRF** | One store for vectors *and* keyword search *and* (future) leads/rate-limits. No separate vector DB to operate. |
| **Frontend** | React + Vite + TypeScript (SPA) | Fast dev loop, typed, trivially deployable as static assets. |
| **Hosting** | Backend on **Render (Docker)**, frontend on **Vercel** | Render keeps a long-lived process (SSE streaming needs it); Vercel is ideal for the static SPA. See the deploy note below on why the backend is *not* on Vercel. |
| **Tooling** | `uv` (Python), `npm` (frontend), `pytest` + `vitest` | `uv` gives reproducible envs and manages the Python version; both sides have tests. |

---

## Design decisions (the director's commentary)

Each decision below follows the same shape: **what I chose · why · what I traded away · how it
extends.** This is the section to read if you want to understand how I think.

### 1. Strict grounding over a "knows everything" chatbot
- **Choice:** the model answers **only** from retrieved passages of my own documents. No
  answer in the context → it politely declines and offers the connect form. The system prompt
  forbids outside knowledge, invented facts, dates, or links.
- **Why:** an ungrounded chatbot representing a real person will confidently hallucinate — the
  worst possible failure for something a recruiter reads. Grounding makes every answer
  traceable to something I actually wrote, and the decline path turns "I don't know" into a
  lead-capture opportunity instead of a lie.
- **Traded away:** breadth. It won't riff on topics I haven't documented. That's the point.
- **Extends to:** citations (return which passage backed each sentence), a per-answer
  confidence signal, or a "sources" drawer in the UI.

### 2. Hybrid retrieval (semantic + keyword) fused with Reciprocal Rank Fusion
- **Choice:** run two searches — **vector similarity** (pgvector) for meaning, and **Postgres
  full-text** for exact terms — then fuse the rankings with **RRF** (`score = Σ 1/(k+rank)`).
- **Why:** pure vector search misses exact tokens (a product name like *"Cougar"*, an acronym
  like *"FICO"*); pure keyword search misses paraphrase ("what's he good at?" vs "skills").
  Hybrid + RRF gets both, and RRF needs no score normalization or tuning to combine them.
- **Traded away:** a little complexity (an RPC that does both legs) vs. a single vector query.
- **Extends to:** a cross-encoder re-ranker on the fused top-k, tunable leg weights, or a
  relevance threshold that widens/narrows the decline gate.

### 3. Server-Sent Events for streaming (not WebSockets, not polling)
- **Choice:** the answer streams token-by-token over SSE (`text/event-stream`), with typed
  events: `token`, `done`, `error` (and `rate_limited` as a 429 before the stream).
- **Why:** the data flow is **one-directional** (server → client) after the request. SSE is
  the simplest thing that fits: plain HTTP, auto-reconnect, no socket lifecycle to manage.
  WebSockets would be over-engineering for a request/response chat; polling would be laggy and
  wasteful.
- **Traded away:** bidirectional mid-stream messaging (which I don't need).
- **Extends to:** a `capture_lead` tool event mid-stream (the agent decides to surface the
  connect form), or per-token metadata.
- **Implementation note:** the browser can't `POST` with the native `EventSource`, so the
  frontend reads the `fetch` `ReadableStream` and parses SSE frames by hand
  ([`streamChat.ts`](frontend/src/lib/streamChat.ts)).

### 4. Synchronous backend, run in FastAPI's threadpool
- **Choice:** the Voyage / Supabase / Anthropic SDKs are used **synchronously**; FastAPI runs
  the sync generator in its threadpool.
- **Why:** for this workload (one provider call chain per request, modest concurrency), sync
  code is dramatically simpler to read and test than threading async through three SDKs. I
  optimized for clarity and correctness over theoretical throughput.
- **Traded away:** max concurrency per instance. Easy to revisit if traffic ever demands it.
- **Extends to:** swap to the async SDK variants and `async def` handlers with no API change.

### 5. Cost guardrails as a first-class design concern
- **Choice:** a **per-session** cap (cookie, 10/day) + a **global daily** cap (100/day),
  enforced **before any provider call**, counters stored durably in Postgres. Full design in
  [`RATE_LIMITING_SPEC.md`](./RATE_LIMITING_SPEC.md).
- **Why:** the endpoint is public and every call costs money. The **global daily cap is the
  hard ceiling on my bill** — worst case ≈ `100 × 1,024 output tokens` on Haiku ≈ **$0.80/day**,
  so $5 of credit survives ~a week even under sustained abuse. Without it, a script is
  unbounded (~$80 for 10k requests). I treated "don't let a stranger bankrupt me" as a real
  requirement, not an afterthought.
- **Traded away:** cookie limits are trivially bypassed (incognito) — but the *global* cap
  still bounds total spend, so per-session is just for fairness, not security.
- **Extends to:** a per-IP tier, a Turnstile bot-challenge, or token-bucket windows — all
  described in the spec. _(Status: designed; implementation is the next slice.)_

### 6. Cheap model by default, escalation by config
- **Choice:** Haiku 4.5 as the default chat model; the model is an env var, and Opus is
  reserved for future escalation.
- **Why:** in a RAG system the retrieved context carries the answer — a fast, cheap model is
  usually enough, and it keeps latency and cost low. Making the model a config value means
  upgrading is a one-line change, not a refactor.
- **Extends to:** dynamic escalation (retry hard questions on Opus), or per-route model choice.

### 7. A UI with a point of view — "Tactile Neo-Brutalism / Zine"
- **Choice:** a hand-made *indie-zine* aesthetic — cream paper, heavy black ink outlines, hard
  offset shadows, one committed vermilion accent, and **hand-drawn doodles** instead of stock
  vector icons. Design system in [`UI_TECHNICAL_SPEC.md`](./UI_TECHNICAL_SPEC.md), reusable
  theme in [`.claude/skills/zine-theme/`](.claude/skills/zine-theme/SKILL.md).
- **Why:** in a web full of near-identical AI-generated UIs, a *human-made* wrapper around a
  custom AI engine is the whole personality of the piece — it signals care and craft. I also
  wanted to avoid the 2026 "beige-and-a-serif" default: beige is the *paper the zine is
  printed on*, and the voice comes from the ink, the doodles, and the type, not the background.
- **Traded away:** the safety of a templated look. Deliberately.
- **Extends to:** a "night edition" dark theme, more doodle motion, an animated hero.
- **Accessibility:** the one real hazard (vermilion is too light for body text on paper) is
  handled — accent is fills/borders/underlines only; body text is high-contrast ink; every
  interactive control has a visible focus ring and a 44px touch target; motion respects
  `prefers-reduced-motion`.

### 8. A hard secrets boundary
- **Choice:** Anthropic / Voyage / Supabase **service-role** keys live only on the backend.
  The frontend gets a single public value: the API base URL.
- **Why:** privileged data and paid APIs must never be reachable from a browser. This is the
  kind of boundary that's cheap to set up early and painful to retrofit.
- **Extends to:** admin auth (Supabase Auth, owner-only) reads privileged data *through* the
  backend after verifying a JWT — never directly from the client.

### 9. Cross-site cookies done properly (Vercel ↔ Render)
- **Choice:** the frontend and backend are different sites, so the session cookie ships as
  `SameSite=None; Secure`, and CORS uses an `allow_origin_regex` that also covers Vercel
  preview deploys. All env-driven — local dev stays on `Lax`.
- **Why:** cross-site auth is where "works on my machine" quietly breaks in production. I made
  it a config decision, documented in [`DEPLOY.md`](./DEPLOY.md), instead of a surprise.
- **Alternative considered:** a Vercel rewrite proxying `/api/*` to Render to make everything
  same-origin (and sidestep cross-site cookies entirely) — documented as an option.

### 10. Pluggable notifications (interface first)
- **Choice (planned):** lead capture writes to the DB via a `Notifier` interface, with a DB
  sink for v1 so email/Slack can be added later without touching the capture logic.
- **Why:** program to an interface so the *delivery mechanism* is a swap, not a rewrite.

---

## Repository layout

```
content/*.md                 the corpus — documents the AI is allowed to answer from
supabase/migrations/         SQL: documents table, pgvector HNSW + FTS indexes, hybrid_search RPC
backend/
  app/
    config.py                all tunables/secrets (nothing hardcoded)
    main.py                  FastAPI app + CORS
    routers/{health,chat}.py HTTP endpoints (chat = SSE)
    services/                embedder · retrieval (hybrid+RRF) · answer (grounding) · pgvector
    sse.py                   SSE frame formatting
  scripts/ingest.py          chunk → embed → replace-by-source
  Dockerfile                 Render (Docker) image — API only, serves from Supabase
  tests/                     pytest (grounding, decline, SSE, validation) — providers mocked
frontend/
  src/
    content/profile.ts       display copy (name, headline, bio, socials, starters)
    lib/streamChat.ts        SSE client (fetch + ReadableStream) + useChatStream hook
    styles/tokens.css        zine design tokens (paper/ink/vermilion, spacing, motion)
    components/              AppShell · profile · chat · doodles · connect · system
  vercel.json                SPA fallback
PRD.md · TECHNICAL_SPEC.md · UI_TECHNICAL_SPEC.md · RATE_LIMITING_SPEC.md · DEPLOY.md · CLAUDE.md
```

`CLAUDE.md` is the project's living memory / progress tracker — a doc-first habit I keep so any
session (or reader) can see exactly what's implemented vs. pending and why.

---

## Run it locally

**Backend** (needs Anthropic + Voyage + Supabase keys):
```bash
cd backend
uv sync                                  # creates .venv, installs deps (uv manages Python 3.12)
cp .env.example .env                     # then fill the keys
# one-time: paste supabase/migrations/0001_init.sql into the Supabase SQL editor and run it
uv run python scripts/ingest.py          # chunk + embed content/*.md into Supabase
uv run uvicorn app.main:app --reload --port 8000
uv run pytest                            # 10 tests, fully mocked (no keys needed)
```

**Frontend:**
```bash
cd frontend
npm install
echo "VITE_API_BASE=http://localhost:8000" > .env   # point at the backend
npm run dev                              # http://localhost:5173
npm test                                 # vitest
```

Deployment (Render + Vercel, with the cross-site cookie / CORS setup) is documented step-by-step
in [`DEPLOY.md`](./DEPLOY.md).

---

## Status & roadmap

Honest state of the build (details in [`CLAUDE.md`](./CLAUDE.md)):

- ✅ **Core RAG loop** — ingest, hybrid retrieval + RRF, grounded answers, decline path.
- ✅ **FastAPI + SSE streaming** `/api/chat` — verified live against real providers.
- ✅ **React "zine" UI** — profile, streaming chat, connect form, doodle kit; a11y + responsive.
- ✅ **Deployed & live** — frontend on [Vercel](https://me-as-a-service.vercel.app/), backend on Render (Docker).
- 🟡 **Rate limiting & guardrails** — designed ([`RATE_LIMITING_SPEC.md`](./RATE_LIMITING_SPEC.md)), implementation is the next slice.
- ⬜ **Lead capture + admin dashboard** — `capture_lead` tool, `/api/leads`, owner-only view.
- ⬜ **Custom domain + end-to-end smoke test.**

## If I kept going — what I'd build next

1. **Ship the guardrails** (the one thing standing between "live" and "safe to share widely").
2. **Agentic lead capture** — let the model *decide* to surface the connect form via a
   `capture_lead` tool event mid-stream, rather than only on a button click.
3. **Citations** — show which passage backed each answer; it makes grounding visible and
   builds trust.
4. **Observability** — request/latency/cost logging so I can see what people ask and what it
   costs.
5. **A re-ranker** on the fused results for sharper retrieval on longer corpora.

---

## About the author

**Arindam Mondal** — Lead Full Stack / AI-ML Engineer at FICO, 12+ years building
enterprise-grade platforms, currently focused on agentic AI, RAG, and MCP tooling.
· [LinkedIn](https://linkedin.com/in/amond) · [GitHub](https://github.com/Arindam-Mondal)
· or just **[ask my AI twin](https://me-as-a-service.vercel.app/)**.

_This is a personal hobby project, built in the open as a demonstration of end-to-end product
engineering. The design docs (`PRD.md`, `TECHNICAL_SPEC.md`, `UI_TECHNICAL_SPEC.md`,
`RATE_LIMITING_SPEC.md`) show the full thought process from product framing to implementation._
