# CLAUDE.md — Project Context & Progress Tracker

> **Read this first.** This file is the living memory of the project. It tells a new
> session what this is, the decisions already made, where things live, and **exactly
> what is implemented vs. pending**. Update the checklists and the "Session log" at the
> end of every working session.

- **Project:** Me-as-a-Service — a live AI agent that answers questions about the owner,
  grounded strictly in owner-provided documents, with rate limiting and agentic lead capture.
- **Specs:** [`PRD.md`](./PRD.md) (product), [`TECHNICAL_SPEC.md`](./TECHNICAL_SPEC.md) (engineering).
- **Last updated:** 2026-06-28

---

## 1. Stack & Key Decisions (locked)

- **Backend:** Python 3.11 + FastAPI (async, SSE streaming). Host: **Render** (Docker).
- **Frontend:** React + Vite + TypeScript (SPA). Host: **Vercel**.
- **LLM:** Anthropic Claude — `claude-haiku-4-5` (default), `claude-opus-4-8` (escalation).
- **Embeddings:** Voyage AI `voyage-3` (1024-dim).
- **Data + search:** Supabase (Postgres) — pgvector (semantic) + Postgres full-text
  (BM25-style lexical), fused via **Reciprocal Rank Fusion (RRF)**.
- **Admin auth:** Supabase Auth (single owner).
- **Rate limits:** per-session (default 10) + global daily (default 100), both env-configurable.
- **Notifications:** stored in DB + private `/admin` dashboard. `Notifier` interface so
  email/Slack can be added later (v1 sink = DB).
- **Ingestion:** Markdown files in `content/` + `scripts/ingest.py`.

> ⚠️ **Secrets boundary:** Anthropic/Voyage/Supabase **service-role** keys are
> backend-only. Frontend uses only the Supabase **anon** key (admin login).

---

## 2. Repo Map (target structure)

```
content/*.md            owner corpus
supabase/migrations/    SQL schema, indexes, RLS, RPCs
backend/app/            FastAPI app (config, services/, routers/)
backend/scripts/ingest.py
backend/tests/
frontend/src/           React app (components/, admin/, lib/, content/profile.ts)
```
See `TECHNICAL_SPEC.md` §3 for the full tree, §4 for the data model, §8 for API contracts.

---

## 3. Environment Setup (for a fresh machine)

1. Copy `.env.example` → `.env`; fill: `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`,
   `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, `OWNER_EMAIL`.
2. **Backend:** `cd backend` → install deps (uv/pip) → `uvicorn app.main:app --reload`.
3. **DB:** apply `supabase/migrations/` (Supabase CLI or MCP); enable `vector` extension.
4. **Ingest:** `python scripts/ingest.py` to load `content/*.md`.
5. **Frontend:** `cd frontend` → `npm install` → `npm run dev`; set `VITE_API_BASE_URL`.

> Update this section with the exact commands once scaffolding (Phase 1) is done.

---

## 4. Progress Tracker

Status key: ✅ done · 🟡 in progress · ⬜ not started

### Phase 0 — Documentation
- ✅ `PRD.md`
- ✅ `TECHNICAL_SPEC.md`
- ✅ `CLAUDE.md` (this file)
- ⬜ Owner review of docs

### Phase 1 — Scaffold
- ⬜ Repo layout (`backend/`, `frontend/`, `content/`, `supabase/`)
- ⬜ `README.md`, `.env.example`
- ⬜ Backend skeleton (FastAPI app, config, `/api/health`)
- ⬜ Backend `Dockerfile`
- ⬜ Frontend skeleton (Vite + TS, base layout)
- ⬜ Test runners wired (pytest, Vitest)

### Phase 2 — Supabase schema
- ⬜ Migration: `documents` (+ pgvector HNSW, FTS GIN)
- ⬜ Migration: `leads`
- ⬜ Migration: `rate_limits`
- ⬜ RLS policies on all tables
- ⬜ `hybrid_search` RPC

### Phase 3 — Ingestion
- ⬜ `embedder.py` (Voyage wrapper)
- ⬜ `scripts/ingest.py` (chunk → embed → upsert)
- ⬜ Sample `content/about.md`
- ⬜ Tests: chunking/overlap/metadata

### Phase 4 — Retrieval
- ⬜ `retrieval.py` (hybrid + RRF, relevance gate)
- ⬜ Tests: fusion ranks relevant chunk; gate triggers on weak retrieval

### Phase 5 — Answer service
- ⬜ Grounded system prompt + context assembly
- ⬜ Claude streaming over SSE
- ⬜ Decline path (insufficient context)
- ⬜ `capture_lead` tool + tool event over SSE
- ⬜ Tests: grounded vs decline (mocked client)

### Phase 6 — Rate limiting
- ⬜ `rate_limit.py` (session cookie issue, atomic upserts)
- ⬜ Enforce before provider calls; 429 contract
- ⬜ Tests: boundaries + daily reset

### Phase 7 — Leads + admin API
- ⬜ `leads.py` + `notifier.py` (ABC + DbNotifier)
- ⬜ `POST /api/leads` (validation)
- ⬜ `GET/PATCH /api/admin/leads` (JWT-gated, OWNER_EMAIL)
- ⬜ Tests: insert, validation, auth required

### Phase 8 — Frontend (public)
- ⬜ `ProfilePanel` (data-driven `profile.ts`)
- ⬜ `ChatPanel` + `MessageList` (SSE streaming, starters)
- ⬜ `ConnectForm` (triggered by `capture_lead`)
- ⬜ `LimitNotice`
- ⬜ Responsive layout + distinctive visual design
- ⬜ Tests: stream render, form validation, limit notice

### Phase 9 — Admin dashboard
- ⬜ Supabase Auth login
- ⬜ Leads table (list, mark read/handled)

### Phase 10 — Deploy
- ⬜ Supabase live (migrations + auth + ingest)
- ⬜ Backend on Render (env wired)
- ⬜ Frontend on Vercel (env wired)
- ⬜ Custom domain
- ⬜ End-to-end smoke test (PRD §6 flows)

---

## 5. Conventions

- **TDD:** write tests before/with implementation for backend logic.
- **Small modules:** one clear purpose per file (see spec §3).
- **Config over hardcoding:** limits, models, top-k all come from env (`config.py`).
- **No secrets in frontend.** Privileged data flows through the backend.
- Keep this tracker honest: only mark ✅ when tested/working.

---

## 6. Open Items / Needs from Owner

- Profile copy: name, headline, catchy bio, avatar, social links.
- Corpus content for `content/*.md` (about, experience, projects).
- Suggested starter questions.
- Visual brand direction (palette, typography) — decided in Phase 8.

---

## 7. Session Log

Append a short entry each session: date — what changed — next step.

- **2026-06-28** — Brainstormed scope; locked stack/decisions; wrote `PRD.md`,
  `TECHNICAL_SPEC.md`, and this `CLAUDE.md`. **Next:** owner reviews docs, then Phase 1
  scaffolding.
