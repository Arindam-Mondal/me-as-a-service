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

## 3. Environment Setup (Slice 1 — backend RAG loop)

> Tooling is **uv** (`pyproject.toml` + `uv.lock`). uv manages the venv **and** the
> Python version — no need for the machine's `py -3` (`python` here is 2.7). Pinned to
> **Python 3.12** via `backend/.python-version`. `backend/.venv` is gitignored;
> `uv.lock` + `.python-version` are committed.

```bash
# 1. Backend env + deps (run from repo root)
cd backend
uv python pin 3.12      # one-time; uv installs 3.12 if it's missing
uv sync                 # creates .venv + uv.lock, installs deps + dev group

# 2. Secrets
cp .env.example .env        # then fill ANTHROPIC_API_KEY, VOYAGE_API_KEY,
                            # SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

# 3. Database (one-time): paste supabase/migrations/0001_init.sql into the
#    Supabase SQL Editor and run it. Creates `documents` + `hybrid_search` RPC.

# 4. Ingest the corpus and query
uv run python scripts/ingest.py
uv run python scripts/query.py "What are Arindam's skills?"

# Tests
uv run pytest
```

---

## 4. Progress Tracker

Status key: ✅ done · 🟡 in progress · ⬜ not started

### Phase 0 — Documentation
- ✅ `PRD.md`
- ✅ `TECHNICAL_SPEC.md`
- ✅ `CLAUDE.md` (this file)
- ⬜ Owner review of docs

### Phase 1 — Scaffold  *(backend subset done in Slice 1)*
- ✅ Repo layout (`backend/`, `content/`, `supabase/`) — frontend dir later
- ✅ `.env.example`, `.gitignore`, `pyproject.toml` + `uv.lock` (uv tooling, Python 3.12)
- ⬜ `README.md`
- ⬜ Backend FastAPI app + `/api/health` (HTTP layer — later slice; CLI-first for now)
- ⬜ Backend `Dockerfile`
- ⬜ Frontend skeleton (Vite + TS, base layout)
- ✅ Test runner wired (pytest); Vitest later

### Phase 2 — Supabase schema  *(documents only in Slice 1)*
- ✅ Migration written: `documents` (+ pgvector HNSW, FTS GIN) — `0001_init.sql`
- ✅ **Applied:** `0001_init.sql` run in Supabase SQL Editor (documents + hybrid_search live)
- ⬜ Migration: `leads`
- ⬜ Migration: `rate_limits`
- ⬜ RLS policies on all tables *(deferred — backend uses service-role key)*
- ✅ `hybrid_search` RPC (vector + FTS + RRF) written in `0001_init.sql`

### Phase 3 — Ingestion
- ✅ `embedder.py` (Voyage wrapper)
- ✅ `scripts/ingest.py` (chunk → embed → replace-by-source)
- ✅ `content/about.md` — **real owner profile** (13 sections; 14 chunks). Superseded placeholder.
- ✅ Tests: chunking (5 passing)
- ✅ Ingest + query verified end-to-end (keys filled, `0001_init.sql` applied in Supabase)

### Phase 4 — Retrieval
- ✅ `retrieval.py` (hybrid + RRF via RPC, empty-result gate)
- ⬜ Automated retrieval test with seeded rows (verified manually via CLI in Slice 1)

### Phase 5 — Answer service
- ✅ Grounded system prompt + context assembly (`answer.py`)
- ✅ Decline path (no-context short-circuit)
- ✅ CLI query path (`scripts/query.py`)
- ⬜ Claude **streaming over SSE** (HTTP slice)
- ⬜ `capture_lead` tool + tool event over SSE (later slice)
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
- **2026-06-28 (Slice 1)** — Built the backend RAG loop, CLI-first: `content/about.md`
  placeholder, `supabase/migrations/0001_init.sql` (`documents` + `hybrid_search` RRF
  RPC), and backend modules (`config`, `supabase_client`, `pgvector`, `chunking`,
  `embedder`, `retrieval`, `answer`) + `scripts/ingest.py` & `scripts/query.py`.
  Chunking tests pass (5); full import/wiring smoke-tested with dummy env. Embeddings
  passed to Postgres as bracketed-string vectors (PostgREST-safe). **Owner actions to
  finish verification:** (1) `cp backend/.env.example backend/.env` + fill keys; (2) run
  `0001_init.sql` in Supabase SQL Editor; (3) `python scripts/ingest.py`; (4)
  `python scripts/query.py "..."`. **Next slice:** FastAPI `/api/chat` + SSE streaming,
  reusing `retrieval`/`answer`.
- **2026-06-28 (tooling)** — Migrated backend from `requirements.txt` + stdlib venv to
  **uv** (`pyproject.toml` + `uv.lock`), pinned **Python 3.12** (`.python-version`).
  Folded `pytest.ini` into `pyproject.toml`; removed `requirements.txt`/`pytest.ini`.
  `uv sync` + `uv run pytest` green (5 passing), imports OK. No app-code changes.
- **2026-07-12** — Owner filled `.env` (Supabase new-format **Secret** key = service role),
  applied `0001_init.sql`. Replaced placeholder `content/about.md` with the **real profile**
  (13 sections → 14 chunks; contact = LinkedIn + connect form, no email/phone; GitHub
  github.com/Arindam-Mondal). **RAG loop verified end-to-end:** semantic (FICO, fitness),
  lexical (Cougar), and decline (off-doc) queries all correct and grounded. **Next slice:**
  FastAPI `/api/chat` + SSE.
