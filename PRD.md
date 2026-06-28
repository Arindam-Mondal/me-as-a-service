# Product Requirements Document — "Me-as-a-Service"

> A live, public AI agent that answers questions about the owner, grounded strictly in
> owner-provided documents. Built to showcase production-grade RAG + agentic workflows.

- **Status:** Draft v1
- **Owner:** Arindam
- **Last updated:** 2026-06-28
- **Related docs:** [`TECHNICAL_SPEC.md`](./TECHNICAL_SPEC.md), [`CLAUDE.md`](./CLAUDE.md)

---

## 1. Vision & Purpose

Me-as-a-Service is a personal website with a twist: instead of a static "About Me"
page, visitors interact with an **AI agent that represents the owner**. The agent
answers questions about the owner's background, skills, experience, and projects —
but **only** using information the owner has explicitly provided. When it cannot
answer, it says so honestly and offers to connect the visitor with the owner directly.

The project has two goals:

1. **Showcase** — a polished, live artifact (shareable on LinkedIn) that demonstrates
   the owner's ability to build a real RAG + agentic system end-to-end.
2. **Learn** — a hands-on vehicle for learning Retrieval-Augmented Generation, hybrid
   search, and agentic tool-use, built to a production standard without over-engineering.

### Design principles
- **Grounded, never fabricated.** The agent only states what the documents support.
- **Production-grade, not gold-plated.** Real auth, rate limits, and tests — but the
  simplest version that is genuinely solid. YAGNI applied ruthlessly.
- **Extensible by content, not by code.** Adding new information about the owner
  (projects, GitHub repos, talks) should mean dropping in a Markdown file and
  re-running ingestion — not changing application logic.

---

## 2. Target Users

| Persona | Goal | Notes |
|---|---|---|
| **Recruiter / hiring manager** | Quickly assess fit, experience, skills | Wants fast, credible answers; may want to reach out |
| **Peer / collaborator** | Understand the owner's work and interests | May ask about specific projects/tech |
| **Curious visitor (from LinkedIn)** | Explore what the owner built | Evaluates the *craft* of the app itself |
| **Owner (admin)** | Review who wanted to connect | Private, authenticated access to leads |

All public users are **anonymous** (no signup). Only the owner authenticates.

---

## 3. Jobs To Be Done (JTBD)

1. **As a visitor, I want a professional landing experience with a chat agent**, so I
   can learn about the owner conversationally.
2. **As a visitor, I want accurate answers drawn only from real information about the
   owner**, so I can trust what the agent tells me — and a graceful "I don't know"
   when the info isn't available.
3. **As the owner, I want the agent rate-limited**, so a single visitor (or abuse)
   cannot exhaust my API budget.
4. **As a visitor who wants to connect — or when the agent can't help — I want to leave
   my name and email**, so the owner can follow up; **and as the owner I want to be
   notified and able to review those leads privately.**

---

## 4. Functional Requirements

### FR1 — Landing page + chat UI  *(JTBD #1)*
- **FR1.1** Two-pane layout: **left** = owner profile/hero (name, headline, a catchy
  bio, avatar, optional social links); **right** = chat panel.
- **FR1.2** Profile content is **data-driven** (a single content file) so it is trivial
  to edit without touching components.
- **FR1.3** Chat panel supports: streaming responses, in-session message history, a
  typing/loading indicator, and **suggested starter questions**.
- **FR1.4** Fully responsive; panes stack vertically on mobile.
- **FR1.5** Distinctive, professional visual design (not a templated default look).
- **FR1.6** Displays remaining-questions context and a clear, friendly notice when a
  rate limit is reached.

### FR2 — Grounded RAG answers  *(JTBD #2)*
- **FR2.1** For each question, retrieve relevant context using **hybrid search**:
  semantic (vector embeddings) **+** lexical (BM25-style full-text), fused via
  **Reciprocal Rank Fusion (RRF)**.
- **FR2.2** Generation is **strictly grounded**: the model answers only from retrieved
  context. It must not use outside/world knowledge to assert facts about the owner.
- **FR2.3** When the answer is not in the documents, the agent responds politely that
  it doesn't have that information, and **offers to connect** the visitor with the owner.
- **FR2.4** Anti-hallucination gate: if retrieval returns nothing sufficiently relevant,
  the agent takes the decline path rather than guessing.
- **FR2.5** Answers are conversational and written in a representative first-/third-person
  voice consistent with a personal assistant for the owner.

### FR3 — Rate limiting  *(JTBD #3)*
- **FR3.1** **Per-session limit:** a server-issued session id (httpOnly cookie) may ask
  at most `SESSION_QUESTION_LIMIT` questions (default **10**, configurable).
- **FR3.2** **Global daily limit:** across all sessions, at most `DAILY_QUESTION_LIMIT`
  questions per UTC day (default **100**, configurable).
- **FR3.3** Both limits are enforced **server-side, before** any embedding/LLM call.
- **FR3.4** When a limit is hit, the API returns a friendly, specific message stating
  which limit was reached and when it resets. The UI surfaces this clearly.
- **FR3.5** Counters are persisted (survive process restarts).

### FR4 — Connect / lead capture  *(JTBD #4, agentic)*
- **FR4.1** The connect flow triggers when **either** the visitor expresses intent to
  connect **or** the agent cannot answer a question.
- **FR4.2** Implemented agentically: the model decides to call a **`capture_lead` tool**;
  the UI then presents a **confirmation + name + email** form (with validation).
- **FR4.3** On submission, the lead is stored with `name`, `email`, optional `message`,
  and lightweight `conversation_context`, plus timestamp.
- **FR4.4** Lead delivery goes through a **Notifier interface** (v1 sink = database),
  so email/Slack notifiers can be added later without changing callers.
- **FR4.5** The owner reviews leads on a private **`/admin`** dashboard, protected by
  **Supabase Auth**: list leads, see details, mark read/handled.
- **FR4.6** Unauthenticated access to `/admin` and admin APIs is rejected.

### FR5 — Extensibility  *(designed-for, not all built in v1)*
- **FR5.1** Corpus is **multi-file and typed** (e.g. `about.md`, `experience.md`,
  `projects.md`, `github.md`); adding content = add a file + re-run ingest.
- **FR5.2** Chunk metadata can carry structured fields (e.g. project URLs, repo links)
  so future answers can include links.
- **FR5.3** Retrieval and answering are content-agnostic — no per-topic code.

---

## 5. Non-Functional Requirements

| # | Requirement |
|---|---|
| NFR1 | **Security:** All provider secrets (Anthropic, Voyage, Supabase service role) live server-side only. Frontend never holds privileged keys. Row-Level Security on all tables. |
| NFR2 | **Privacy:** Lead emails are PII; readable only by the authenticated owner. No third-party analytics on visitor messages in v1. |
| NFR3 | **Performance:** First token of a chat response should typically begin streaming within ~2s under normal conditions. |
| NFR4 | **Reliability:** Rate-limit counters and leads are durably persisted. Graceful, user-friendly errors on provider failures. |
| NFR5 | **Cost control:** Rate limits + a fast default model (`claude-haiku-4-5`) keep spend bounded. |
| NFR6 | **Testability:** Core logic (retrieval fusion, grounding decision, rate-limit boundaries, lead capture) covered by automated tests with mocked providers. |
| NFR7 | **Maintainability:** Small, single-purpose modules with clear interfaces; documented env config. |
| NFR8 | **Portability:** Backend containerized and host-agnostic (Render now, movable to Railway/Fly). |

---

## 6. Key User Flows

### 6.1 Answerable question (happy path)
1. Visitor opens the site → profile + chat with starter questions.
2. Visitor asks a question.
3. Backend checks rate limits → embeds query → hybrid retrieval (RRF) → grounded
   Claude call → streams a grounded answer.
4. Session question counter increments.

### 6.2 Unanswerable question → connect
1. Visitor asks something not covered by the documents.
2. Retrieval is weak/empty → agent declines politely and offers to connect.
3. Agent calls `capture_lead`; UI shows the connect form.
4. Visitor submits name + email → stored as a lead → confirmation shown.

### 6.3 Explicit "I want to connect"
1. Visitor says they'd like to get in touch.
2. Agent recognizes intent → calls `capture_lead` → form → stored lead.

### 6.4 Rate limit reached
1. Visitor exceeds session or global daily limit.
2. Backend blocks before any provider call; returns which limit + reset time.
3. UI shows a friendly notice (and may still offer the connect form).

### 6.5 Owner reviews leads
1. Owner visits `/admin` → authenticates via Supabase Auth.
2. Sees a list of leads with details; can mark read/handled.

---

## 7. Success Criteria

- A visitor can ask several questions and receive accurate, grounded answers.
- Off-document questions reliably produce a polite decline + connect offer (no
  hallucinated facts about the owner).
- Hitting either rate limit produces the correct block + message, and limits reset.
- A submitted connect form reliably appears in the owner's authenticated dashboard.
- The app is deployed at a public URL suitable to share on LinkedIn.
- Adding a new content file + re-running ingest makes new information answerable, with
  no code changes.

---

## 8. Out of Scope (v1)

- Multi-tenant / multiple owners.
- Public user accounts or login.
- In-app document upload UI (corpus is repo Markdown + ingest script in v1).
- Email/Slack lead notifications (interface designed for it; sink is DB in v1).
- Conversation persistence across sessions / long-term memory.
- Voice, multilingual, or analytics dashboards.

---

## 9. Future Enhancements

- Admin **upload UI** for documents (PDF/Markdown), live re-ingestion.
- **Email/Slack** notifier sinks behind the existing Notifier interface.
- Rich answers with **project cards / GitHub links** rendered from chunk metadata.
- Per-IP rate-limit tier for stronger abuse resistance.
- Lightweight **analytics** (popular questions, answer/decline ratio).
- Optional **citations** showing which document a fact came from.

---

## 10. Open Questions

- Final owner profile copy (bio, headline, avatar, social links) — owner to supply.
- Exact set of suggested starter questions.
- Visual brand direction (palette, typography) — decided during the frontend phase.
