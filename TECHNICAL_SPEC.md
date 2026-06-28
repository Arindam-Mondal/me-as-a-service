# Technical Specification — "Me-as-a-Service"

- **Status:** Draft v1
- **Last updated:** 2026-06-28
- **Related docs:** [`PRD.md`](./PRD.md), [`CLAUDE.md`](./CLAUDE.md)

This document is the engineering source of truth: architecture, modules, data model,
API contracts, algorithms, config, and deployment. It implements the requirements in
`PRD.md` (referenced as FRx).

---

## 1. Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | **React + Vite + TypeScript** | SPA; deploys to Vercel |
| Backend | **Python 3.11 + FastAPI** | Async; streaming responses |
| LLM (generation) | **Anthropic Claude** | `claude-haiku-4-5` default; `claude-opus-4-8` escalation |
| Embeddings | **Voyage AI** `voyage-3` | 1024-dim vectors; query vs document input types |
| Database | **Supabase (Postgres 15)** | Single store: vectors, leads, rate limits |
| Vector search | **pgvector** | HNSW or IVFFlat index on embedding |
| Lexical search | **Postgres full-text** (`tsvector`/`ts_rank`) | BM25-style ranking |
| Auth (admin) | **Supabase Auth** | Single owner; magic link / email+password |
| Backend host | **Render** (free tier) | Containerized; movable to Railway/Fly |
| Frontend host | **Vercel** | Static SPA + env for API base URL |

### Why Postgres FTS instead of true BM25
Supabase does not ship the ParadeDB `pg_search` (BM25) extension. We use Postgres
native full-text (`tsvector` + `ts_rank`) for lexical ranking and fuse it with vector
similarity via RRF. This is documented to users/readers as **"BM25-style hybrid search."**
If true BM25 is later required, the lexical leg can be swapped without touching the
fusion or answer layers.

---

## 2. High-Level Architecture

```
                         ┌──────────────────────────────────────────┐
   Browser (Vercel)      │                FastAPI (Render)          │
 ┌───────────────────┐   │                                          │
 │ ProfilePanel      │   │  POST /api/chat ─► RateLimiter ─► Embedder│──► Voyage AI
 │ ChatPanel (SSE)   │◄──┼─ stream           │            └► Retrieval├──► Supabase
 │ ConnectForm       │   │                   └► AnswerService ───────┼──► Anthropic
 │ /admin (Supa Auth)│   │  POST /api/leads ─► LeadService ─► Notifier├──► Supabase
 └───────────────────┘   │  GET  /api/admin/leads ─► (auth) ─────────┼──► Supabase
                         └──────────────────────────────────────────┘
                                          ▲
   scripts/ingest.py (offline):  content/*.md ─► chunk ─► Voyage embed ─► Supabase upsert
```

---

## 3. Repository Layout

```
me-as-a-service/
├── PRD.md
├── TECHNICAL_SPEC.md
├── CLAUDE.md
├── README.md
├── .env.example
├── content/                     # owner corpus (Markdown)
│   ├── about.md
│   ├── experience.md
│   └── projects.md
├── supabase/
│   └── migrations/              # SQL migrations (schema, indexes, RLS, RPCs)
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, router wiring
│   │   ├── config.py           # pydantic-settings (env)
│   │   ├── deps.py             # shared deps (supabase client, session)
│   │   ├── models.py           # pydantic request/response models
│   │   ├── services/
│   │   │   ├── embedder.py     # Voyage wrapper
│   │   │   ├── retrieval.py    # hybrid search + RRF
│   │   │   ├── answer.py       # grounded prompt + Claude + tools
│   │   │   ├── rate_limit.py   # session + global daily
│   │   │   ├── leads.py        # persist leads
│   │   │   └── notifier.py     # Notifier ABC + DbNotifier
│   │   └── routers/
│   │       ├── chat.py
│   │       ├── leads.py
│   │       ├── admin.py
│   │       └── health.py
│   ├── scripts/
│   │   └── ingest.py
│   └── tests/
└── frontend/
    ├── package.json
    ├── index.html
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── content/profile.ts  # editable owner profile data
    │   ├── lib/api.ts          # typed fetch + SSE client
    │   ├── components/
    │   │   ├── ProfilePanel.tsx
    │   │   ├── ChatPanel.tsx
    │   │   ├── MessageList.tsx
    │   │   ├── ConnectForm.tsx
    │   │   └── LimitNotice.tsx
    │   └── admin/
    │       ├── AdminApp.tsx
    │       ├── Login.tsx
    │       └── LeadsTable.tsx
    └── tests/
```

---

## 4. Data Model (Supabase / Postgres)

### 4.1 `documents` — corpus chunks
```sql
create extension if not exists vector;

create table documents (
  id           bigserial primary key,
  source_file  text not null,                 -- e.g. 'about.md'
  title        text,                           -- nearest heading
  content      text not null,                  -- chunk text
  metadata     jsonb not null default '{}',    -- {url, repo, tags, ...}
  embedding    vector(1024) not null,          -- voyage-3
  fts          tsvector generated always as
                 (to_tsvector('english', coalesce(title,'') || ' ' || content)) stored,
  created_at   timestamptz not null default now()
);

create index documents_embedding_idx
  on documents using hnsw (embedding vector_cosine_ops);
create index documents_fts_idx
  on documents using gin (fts);
```

### 4.2 `leads` — connect submissions
```sql
create table leads (
  id                   bigserial primary key,
  name                 text not null,
  email                text not null,
  message              text,
  conversation_context jsonb not null default '[]',
  status               text not null default 'new',   -- new | read | handled
  created_at           timestamptz not null default now()
);
```

### 4.3 `rate_limits` — counters
```sql
create table rate_limits (
  key         text not null,                  -- session id, or 'global'
  kind        text not null,                  -- 'session' | 'global'
  window_date date not null default (now() at time zone 'utc')::date,
  count       int  not null default 0,
  updated_at  timestamptz not null default now(),
  primary key (key, kind, window_date)
);
```

### 4.4 Row-Level Security
- **All tables:** RLS enabled.
- `documents`: no public client access; backend uses the **service-role** key (bypasses
  RLS) for retrieval. (Optionally a read-only RPC for retrieval.)
- `leads`: `insert` only via backend (service role); `select` policy restricts reads to
  the authenticated owner (matched by owner email / role). Admin reads go through the
  backend using service role **after** verifying the caller's Supabase JWT.
- `rate_limits`: backend (service role) only.

> **Secrets boundary:** the **service-role key never reaches the browser**. The frontend
> uses only the **anon key** for admin login (Supabase Auth). Admin data is fetched
> through the backend, which validates the user's JWT.

---

## 5. Retrieval — Hybrid Search + RRF (FR2.1)

### 5.1 Algorithm
1. Embed the query with Voyage (`input_type="query"`).
2. **Vector leg:** top-`N` chunks by cosine similarity (pgvector).
3. **Lexical leg:** top-`N` chunks by `ts_rank` against `plainto_tsquery(query)`.
4. **Fuse with Reciprocal Rank Fusion:** for each doc `d`,
   `score(d) = Σ_legs 1 / (k + rank_leg(d))`, with `k = 60` (standard).
5. Return top-`K` fused chunks (default `K = 5`).
6. **Relevance gate:** if the best fused result is below a minimum threshold (or both
   legs return nothing), signal "insufficient context" → answer layer takes decline path.

### 5.2 Implementation
- Implemented as a **Postgres RPC** (`hybrid_search(query_embedding, query_text, n, k)`)
  returning fused rows, **or** as two queries fused in Python. RPC preferred (one round
  trip, ranking in DB). Tunables (`N`, `K`, `k_rrf`, threshold) come from config.

---

## 6. Answer Service — Grounding + Agentic Tools (FR2, FR4)

### 6.1 Prompt structure
- **System prompt** establishes: the assistant represents the owner; it must answer
  **only** from the provided `<context>`; if the answer isn't there, it must say so and
  offer to connect; it must never invent facts about the owner.
- **Context block:** the retrieved chunks (with source labels).
- **User turn:** the visitor's question (+ short prior turns for continuity).

### 6.2 Grounding gate
- If retrieval signals insufficient context, the service short-circuits to a templated
  polite decline + connect offer (and may emit a `capture_lead` tool event), avoiding a
  wasted generation that could hallucinate.

### 6.3 Tool use — `capture_lead`
```jsonc
{
  "name": "capture_lead",
  "description": "Call when the visitor wants to connect with the owner, or when you cannot answer and should offer a human follow-up.",
  "input_schema": {
    "type": "object",
    "properties": {
      "reason": { "type": "string", "enum": ["user_requested", "cannot_answer"] },
      "suggested_message": { "type": "string" }
    },
    "required": ["reason"]
  }
}
```
- When Claude emits this tool call, the streamed response includes a structured event
  (`{"type":"capture_lead", ...}`) that the frontend uses to render `ConnectForm`.
- The tool does **not** itself write a lead; the actual write happens via
  `POST /api/leads` after the visitor submits the form (consent + validated email).

### 6.4 Streaming
- Claude streamed via the Anthropic SDK; FastAPI relays as **Server-Sent Events**.
- Event types over the wire: `token` (text delta), `capture_lead` (tool trigger),
  `done`, `error`, `rate_limited`.

---

## 7. Rate Limiting (FR3)

### 7.1 Identity
- On first chat request without a session cookie, the backend issues an **httpOnly,
  SameSite=Lax** cookie `sid` (random UUID). Used for the per-session counter.

### 7.2 Enforcement (before any provider call)
```
on POST /api/chat:
  sid = cookie or new
  today = utc_date()
  session_count = get(rate_limits, key=sid, kind='session')   # all-time per session
  global_count  = get(rate_limits, key='global', kind='global', window=today)
  if session_count >= SESSION_QUESTION_LIMIT: return 429 {limit:'session', reset:'per-session'}
  if global_count  >= DAILY_QUESTION_LIMIT:   return 429 {limit:'daily',  reset: next_utc_midnight}
  ... proceed; on success atomically increment both counters ...
```
- Increments are **atomic upserts** (`insert ... on conflict ... do update count = count + 1`).
- Session limit is lifetime-per-session (cookie); global limit resets daily by
  `window_date`. Both thresholds from env (FR3.2).

### 7.3 Response
- `429` with JSON `{ "error": "rate_limited", "limit": "session|daily", "message": "...", "reset_at": "<iso8601|null>" }`.
- Frontend renders `LimitNotice` and may still offer the connect form.

---

## 8. API Contracts

Base URL: backend origin (e.g. `https://me-api.onrender.com`). All JSON unless noted.

### 8.1 `POST /api/chat`  *(streaming, SSE)*
**Request**
```json
{ "message": "What did you work on at Acme?", "history": [{"role":"user|assistant","content":"..."}] }
```
**Cookies:** `sid` (issued if absent).
**Response:** `text/event-stream`, events:
```
event: token        data: {"text":"He led "}
event: capture_lead data: {"reason":"cannot_answer","suggested_message":"..."}
event: done         data: {"session_remaining": 7}
event: error        data: {"message":"..."}
```
**Errors:** `429` (rate limited) returned before stream starts.

### 8.2 `POST /api/leads`
**Request**
```json
{ "name":"Jane Doe", "email":"jane@x.com", "message":"Loved this!", "conversation_context":[...] }
```
**Response:** `201 { "ok": true, "id": 42 }`  ·  **Validation:** `400` on bad email/missing name.

### 8.3 `GET /api/admin/leads`  *(auth required)*
**Headers:** `Authorization: Bearer <supabase_jwt>`.
**Response:** `200 { "leads": [ { "id","name","email","message","status","created_at", ... } ] }`
**Errors:** `401` if JWT missing/invalid.

### 8.4 `PATCH /api/admin/leads/{id}`  *(auth required)*
**Request:** `{ "status": "read|handled" }` → `200 { "ok": true }`.

### 8.5 `GET /api/health`
**Response:** `200 { "status":"ok", "version":"..." }`.

---

## 9. Ingestion Pipeline (FR5)

`scripts/ingest.py`:
1. Read every `content/*.md`.
2. **Chunk:** split on headings, then into ~500-token windows with ~50-token overlap;
   capture nearest heading as `title` and any front-matter as `metadata`.
3. **Embed:** Voyage `voyage-3` with `input_type="document"` (batched).
4. **Upsert** into `documents` (idempotent: clear+reload per `source_file`, or hash-diff).
5. Print a summary (files, chunks, tokens). Re-runnable anytime content changes.

---

## 10. Configuration (`.env`)

| Variable | Scope | Default | Purpose |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | backend | — | Claude generation |
| `VOYAGE_API_KEY` | backend | — | Embeddings |
| `SUPABASE_URL` | backend + frontend | — | Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | **backend only** | — | Privileged DB access |
| `SUPABASE_ANON_KEY` | frontend | — | Admin auth (Supabase Auth) |
| `CHAT_MODEL` | backend | `claude-haiku-4-5` | Default generation model |
| `ESCALATION_MODEL` | backend | `claude-opus-4-8` | Optional higher-quality model |
| `EMBEDDING_MODEL` | backend | `voyage-3` | Embedding model |
| `SESSION_QUESTION_LIMIT` | backend | `10` | Per-session cap (FR3.1) |
| `DAILY_QUESTION_LIMIT` | backend | `100` | Global daily cap (FR3.2) |
| `RETRIEVAL_TOP_N` | backend | `20` | Per-leg candidates |
| `RETRIEVAL_TOP_K` | backend | `5` | Final fused chunks |
| `RETRIEVAL_MIN_SCORE` | backend | tuned | Relevance gate threshold |
| `RRF_K` | backend | `60` | RRF constant |
| `ALLOWED_ORIGINS` | backend | frontend URL | CORS |
| `OWNER_EMAIL` | backend | — | Authorizes admin reads |
| `VITE_API_BASE_URL` | frontend | — | Backend origin |

---

## 11. Security Summary

- Provider/service-role secrets are **backend-only**; never shipped to the browser.
- Admin endpoints validate the Supabase **JWT** and authorize against `OWNER_EMAIL`.
- RLS on all tables; privileged writes/reads go through the backend.
- Input validation on `/api/leads` (email format, length limits) to prevent junk/abuse.
- CORS restricted to the known frontend origin(s).
- Rate limiting bounds both abuse and spend.

---

## 12. Testing Strategy (NFR6)

- **Backend (pytest):**
  - Retrieval RRF fusion ranks a known-relevant chunk above noise (seeded rows).
  - Grounding: in-context question → grounded answer; off-context → decline path
    (Anthropic client mocked).
  - Rate limits: boundary tests (`limit-1`, `limit`, `limit+1`) for session and global;
    daily reset by `window_date`.
  - Leads: valid insert persists; invalid email rejected; admin read requires valid JWT.
  - Ingestion: chunking boundaries/overlap and metadata extraction (pure-function tests).
- **Frontend (Vitest + RTL):** chat stream rendering, ConnectForm validation, LimitNotice.
- **End-to-end (manual + scripted):** the flows in PRD §6 against a live Supabase.

---

## 13. Deployment Topology

| Component | Host | Notes |
|---|---|---|
| Frontend SPA | **Vercel** | Build Vite; set `VITE_API_BASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` |
| Backend API | **Render** | Docker; set all backend env; long-running for SSE |
| Database/Vectors/Auth | **Supabase** | Run migrations; enable `vector`; configure Auth (single owner) |
| Corpus | repo `content/*.md` | Re-run `ingest.py` after changes |

CI (optional, later): run backend + frontend tests on push; deploy on green.

---

## 14. Sequence: a chat request

```
Browser ──POST /api/chat (sid cookie)──► FastAPI
  FastAPI ─► RateLimiter.check(sid, global)         [429 if exceeded]
  FastAPI ─► Embedder.embed(query)                  ──► Voyage
  FastAPI ─► Retrieval.hybrid_search(...)           ──► Supabase (RPC, RRF)
  FastAPI ─► AnswerService.stream(context, history) ──► Anthropic (tools)
  FastAPI ◄─ token deltas / capture_lead tool event
  Browser ◄─ SSE: token... [capture_lead] done(session_remaining)
  FastAPI ─► RateLimiter.increment(sid, global)     (on success)
```
