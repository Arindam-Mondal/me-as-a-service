# CLAUDE.md — Project Context & Progress Tracker

> **Read this first.** This file is the living memory of the project. It tells a new
> session what this is, the decisions already made, where things live, and **exactly
> what is implemented vs. pending**. Update the checklists and the "Session log" at the
> end of every working session.

- **Project:** Me-as-a-Service — a live AI agent that answers questions about the owner,
  grounded strictly in owner-provided documents, with rate limiting and agentic lead capture.
- **Specs:** [`PRD.md`](./PRD.md) (product), [`TECHNICAL_SPEC.md`](./TECHNICAL_SPEC.md) (engineering),
  [`UI_TECHNICAL_SPEC.md`](./UI_TECHNICAL_SPEC.md) (frontend/theme).
- **UI theme:** Tactile Neo-Brutalism "Zine" — beige paper, black ink outlines + hard shadows,
  Riso-Vermilion `#FF4D2E` accent, hand-drawn doodles; Shantell Sans + Hanken Grotesk; mobile-first,
  light-only. Reusable theme skill: [`.claude/skills/zine-theme/SKILL.md`](./.claude/skills/zine-theme/SKILL.md).
  Build UI via the `impeccable` + `frontend-design` skills.
- **Last updated:** 2026-07-12

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
- ✅ Backend FastAPI app + `/api/health` (Slice 2 — `main.py`, CORS, `deps.py`,
  `models.py`, `sse.py`, `version.py`, `routers/{health,chat}.py`; verified live)
- ✅ Backend `Dockerfile` (+ `.dockerignore`) for Render Docker runtime
- ✅ Frontend skeleton (Vite + TS, base layout) — full zine UI built in Phase 8
- ✅ Test runner wired (pytest 10 passing; Vitest 5 passing)

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
- ✅ Claude **streaming over SSE** (`stream_answer()` + `POST /api/chat`; token/done/error events)
- ⬜ `capture_lead` tool + tool event over SSE (later slice)
- ✅ Tests: grounded vs decline (mocked client) — `test_chat_api.py` (5 passing) + hermetic `conftest.py`

### Phase 6 — Rate limiting
- ⬜ `rate_limit.py` (session cookie issue, atomic upserts)
- ⬜ Enforce before provider calls; 429 contract
- ⬜ Tests: boundaries + daily reset

### Phase 7 — Leads + admin API
- ⬜ `leads.py` + `notifier.py` (ABC + DbNotifier)
- ⬜ `POST /api/leads` (validation)
- ⬜ `GET/PATCH /api/admin/leads` (JWT-gated, OWNER_EMAIL)
- ⬜ Tests: insert, validation, auth required

### Phase 8 — Frontend (public)  *(theme + spec locked — see `UI_TECHNICAL_SPEC.md`)*
- ✅ Scaffold (Vite+TS, `@fontsource-variable` Shantell+Hanken, tokens.css/global.css,
  AppShell + page-frame, `profile.ts`). Build + typecheck green.
- ✅ Doodle SVG kit (`components/doodles/` — ring, squiggle, arrow, sparkle, bubble, gh, in, send, ink)
- ✅ `ProfilePanel` / `Avatar` (doodle ring + initials fallback) / `SocialLinks`
- ✅ `ChatPanel` + `MessageList` + `Message` (markdown+caret) + `Composer` + `StarterQuestions`
      — real SSE streaming via `lib/streamChat.ts` + `useChatStream` hook
- ✅ `ConnectForm` (native `<dialog>`, client validation) — `capture_lead` auto-trigger + `POST /api/leads` are later slices
- ✅ `LimitNotice` (client wired to HTTP 429; backend 429 lands in Phase 6)
- ✅ Responsive layout (mobile stacked → two-panel desktop spread) + zine visual design
- 🟡 Tests: `streamChat` parsing (3) + App render/connect (2) passing; form-validation + limit-notice
      unit tests still to add

### Phase 9 — Admin dashboard
- ⬜ Supabase Auth login
- ⬜ Leads table (list, mark read/handled)

### Phase 10 — Deploy  *(config prepared — see `DEPLOY.md`)*
- ✅ Supabase live (`0001_init.sql` applied; corpus ingested)
- ✅ Deploy config prepared: `backend/Dockerfile` + `.dockerignore`; cross-site cookie
  (`COOKIE_SAMESITE`/`COOKIE_SECURE`) + `ALLOWED_ORIGIN_REGEX` in `config.py`/`main.py`/`chat.py`;
  `frontend/vercel.json`; `DEPLOY.md` runbook
- ⬜ Backend on Render (owner: create Docker service + env — runbook step 1)
- ⬜ Frontend on Vercel (owner: import repo, set `VITE_API_BASE` — runbook step 2)
- ⬜ Custom domain
- ⬜ End-to-end smoke test (PRD §6 flows) after deploy
- ⚠️ **No rate limiting yet (Phase 6)** — public URL = uncapped provider spend; gate before wide sharing

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
- ✅ Visual brand direction — **decided**: Tactile Neo-Brutalism "Zine" (see top of file +
  `UI_TECHNICAL_SPEC.md`). Still needed: avatar image; confirm starter questions + headline/bio microcopy.

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
- **2026-07-12 (Slice 2 — in progress)** — Started the FastAPI + SSE streaming slice
  (plan approved). Done so far: added `fastapi` + `uvicorn[standard]` to `pyproject.toml`;
  added `allowed_origins` (CORS) to `config.py`. **Still to write:** `app/main.py`,
  `app/sse.py`, `app/deps.py`, `app/models.py`, `app/routers/{health,chat}.py`,
  `stream_answer()` in `answer.py`, and `tests/{conftest,test_chat_api}.py`; then `uv sync`
  + verify (curl SSE + pytest). Design: stays synchronous; reuses `retrieval`/`answer`;
  issues `sid` cookie as rate-limit foundation.
- **2026-07-12 (Slice 2 — DONE ✅)** — Completed + verified the FastAPI + SSE slice. Wrote
  `app/{main,deps,models,sse,version}.py` and `app/routers/{health,chat}.py`;
  `stream_answer()` streams Anthropic text deltas as `token` SSE frames → `done`, with an
  `error` frame on failure; `/api/chat` plants an httpOnly `sid` cookie (rate-limit
  foundation). Tests: `tests/{conftest,test_chat_api}.py` — 5 passing (health, token
  stream, decline, error, 422 validation), fully mocked/hermetic. **Verified LIVE:**
  `GET /api/health` OK; `POST /api/chat` streamed a real grounded answer (Voyage→Supabase
  hybrid→Claude Haiku) about Arindam's skills, terminating cleanly. **Next:** frontend —
  UI theme + tech spec first (this session).
- **2026-07-12 (UI planning — in progress)** — Kicked off Phase 8 frontend planning.
  Locked visual direction: **Tactile Neo-Brutalism "Zine" aesthetic** (beige/paper base +
  heavy black outlines + hand-drawn doodle overlays), **mobile-first & responsive**. Using
  the `impeccable` + `frontend-design` skills for craft. Producing `UI_TECHNICAL_SPEC.md`
  and a reusable theme skill file. **Next:** confirm accent color / fonts / dark-mode forks,
  then write the two design docs, then build the React UI.
- **2026-07-12 (Phase 8 UI — built ✅)** — Locked forks: **Riso Vermilion `#FF4D2E`** accent,
  **Shantell Sans + Hanken Grotesk**, **light-only**. Wrote `UI_TECHNICAL_SPEC.md` +
  `.claude/skills/zine-theme/SKILL.md`. Built the full React+Vite+TS `frontend/`: tokens +
  global zine CSS, doodle SVG kit, `streamChat`/`useChatStream` (fetch+ReadableStream SSE),
  ProfilePanel/Avatar/SocialLinks, ChatPanel/MessageList/Message(markdown+caret)/Composer/
  StarterQuestions, ConnectForm (`<dialog>`), LimitNotice, AppShell page-frame. **Verified:**
  `npm run build` (tsc+vite) green, fonts bundled; `npm test` 5 passing (streamChat parse ×3,
  App render + connect ×2); dev server serves on :5173. **Not yet done:** live browser QA with
  backend :8000, avatar image, `POST /api/leads` wiring (Phase 7), backend 429 (Phase 6).
  **Next:** open http://localhost:5173 against the running backend for real chat + a11y/responsive polish.
- **2026-07-12 (deploy prep ✅)** — Prepared full-stack deploy (frontend→Vercel, backend→Render).
  Backend: `Dockerfile` + `.dockerignore` (Render Docker, serves API only from Supabase);
  env-driven cross-site cookie (`cookie_samesite`/`cookie_secure`) + CORS `allowed_origin_regex`
  (covers `*.vercel.app` previews) in `config.py`/`main.py`/`chat.py`; `.env.example` updated.
  Frontend: `vercel.json` SPA fallback; deploys point `VITE_API_BASE` at the Render URL. Wrote
  `DEPLOY.md` runbook. **Verified:** `uv run pytest` 10 pass, `npm run build` green. **Owner to
  do (needs your logins):** run the DEPLOY.md steps (Render service + Vercel import + env vars).
  **Risk flagged:** no rate limiting yet (Phase 6) → cap before making the URL public.
