# UI_TECHNICAL_SPEC.md — Me-as-a-Service Frontend

> Engineering + design spec for the public web UI (Phase 8). Pairs with
> [`PRD.md`](./PRD.md), [`TECHNICAL_SPEC.md`](./TECHNICAL_SPEC.md) (API contracts), and the
> reusable theme skill at [`.claude/skills/zine-theme/SKILL.md`](./.claude/skills/zine-theme/SKILL.md).
> **Design craft is driven by the `impeccable` + `frontend-design` skills** — invoke them
> when building UI (see §12).

- **Register:** brand (portfolio — the design *is* the product).
- **Theme:** **Tactile Neo-Brutalism — the "Zine" aesthetic.** Beige *paper* base, heavy
  black ink outlines, hard offset shadows, and **hand-drawn doodle overlays** for avatar,
  social links, chat indicators, and accents. It should read as a human-made indie zine
  wrapped around a custom AI chat engine — raw + personal, deliberately *not* a uniform AI UI.
- **Approach:** **mobile-first & responsive**, light-only ("day zine"), accessible (WCAG AA).
- **Last updated:** 2026-07-12

---

## 1. Design Rationale (why this isn't generic beige)

Plain beige/cream as a whole palette is the #1 "AI made this" tell. We escape it by
treating **beige as the paper the zine is printed on**, and carrying all the voice through:

1. **One loud committed accent** — Riso Vermilion `#FF4D2E` — on buttons, links (as marker
   underline), active borders, and doodle pops.
2. **Heavy black ink** — 2–3px outlines + **hard offset shadows** (no blur) on every
   tactile element (the neo-brutal signature).
3. **Hand-drawn everything that would normally be a vector icon** — avatar frame, GitHub /
   LinkedIn marks, chat-bubble tails, arrows, squiggle underlines, sparkles.
4. **A genuinely hand-drawn display face** — Shantell Sans — against a crisp grotesque body.

**AI-slop bans enforced here:** no gradient text, no glassmorphism, no side-stripe borders,
no tiny uppercase tracked eyebrows above every section, no identical card grids, no
hero-metric template. (See `impeccable` absolute bans + the theme skill's Do/Don't.)

---

## 2. Design Tokens

Authoritative values are **hex**; OKLCH provided per the design system (approximate, for
tuning). Define once as CSS custom properties on `:root`.

```css
:root {
  /* Surfaces — the "paper" */
  --paper:      #F4ECD8;  /* oklch(0.93 0.03 92)  page background        */
  --paper-2:    #ECE3CC;  /* oklch(0.91 0.035 92) panels / raised cards  */
  --paper-edge: #E3D8BC;  /* oklch(0.88 0.04 92)  hairline / deep insets */

  /* Ink — text + borders + shadows */
  --ink:        #141210;  /* oklch(0.18 0.006 70) primary text, borders, shadow */
  --ink-soft:   #4A443A;  /* oklch(0.38 0.02 80)  secondary text (≥4.5:1 on paper) */

  /* Accent — Riso Vermilion */
  --accent:      #FF4D2E; /* oklch(0.66 0.21 32) */
  --accent-deep: #D93A1E; /* oklch(0.58 0.20 32) hover/active fill        */
  --on-accent:   #141210; /* text ON vermilion = INK (see §2.1 contrast)  */

  /* Feedback (kept in-palette, still bordered/shadowed) */
  --ok:    #2E7D46;
  --warn:  #C77400;
  --error: #C02A1B;

  /* Brutalist structure */
  --border-w:   3px;                 /* 2px on very small controls        */
  --radius:     4px;                 /* near-square; doodle SVGs carry the organic wobble */
  --shadow:     4px 4px 0 0 var(--ink);
  --shadow-sm:  2px 2px 0 0 var(--ink);
  --shadow-lg:  6px 6px 0 0 var(--ink);

  /* Spacing — 4px base, varied for rhythm (not a flat scale) */
  --s-1: 0.25rem; --s-2: 0.5rem; --s-3: 0.75rem; --s-4: 1rem;
  --s-5: 1.5rem;  --s-6: 2rem;   --s-8: 3rem;    --s-10: 4rem;

  /* Motion */
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);   /* ease-out-quint */
  --dur-fast: 120ms; --dur: 220ms; --dur-slow: 420ms;

  /* Z-index scale (semantic, never 9999) */
  --z-sticky: 100; --z-backdrop: 200; --z-dialog: 300; --z-toast: 400; --z-tooltip: 500;
}
```

### 2.1 Contrast rules (MUST follow — vermilion is a trap)

- **Vermilion is NOT a text color on paper.** `#FF4D2E` on `#F4ECD8` is ~2.5:1 — fails.
  Use accent for **fills, borders, underlines, and doodle strokes only**. Links are
  **ink text with a vermilion marker underline**, never vermilion body text.
- **Text on a vermilion fill = ink (`#141210`)**, and keep it **bold** (buttons). Ink on
  vermilion ≈ 4.4:1 (AA for normal, comfortably AA for bold/large). Avoid white-on-vermilion
  for anything below large-bold.
- **Body text = `--ink`; secondary = `--ink-soft`** (verified ≥4.5:1 on both paper tones).
  Never lighten body text "for elegance."
- **Placeholders** use `--ink-soft`, not a light gray.

---

## 3. Typography

Self-host via `@fontsource` (no CDN dependency; fast, offline-safe).

- **Display / personality:** **Shantell Sans** (`@fontsource-variable/shantell-sans`) —
  hand-drawn. Headings, name, starter chips, doodle labels, the streaming "…thinking" tag.
- **Body / UI:** **Hanken Grotesk** (`@fontsource-variable/hanken-grotesk`) — chat text,
  paragraphs, form fields, buttons. Crisp and readable where Shantell would tire the eye.

```css
:root {
  --font-display: "Shantell Sans Variable", "Comic Sans MS", cursive;
  --font-body:    "Hanken Grotesk Variable", ui-sans-serif, system-ui, sans-serif;
}
```

**Scale** — fluid `clamp()`, ratio ≥1.25, display max ≤6rem, letter-spacing ≥ -0.04em:

| Role        | Font     | Size                                  | Notes |
|-------------|----------|---------------------------------------|-------|
| Display h1  | Display  | `clamp(2.5rem, 7vw, 4rem)`            | `text-wrap: balance`, weight 700 |
| h2          | Display  | `clamp(1.75rem, 4vw, 2.5rem)`         | section titles |
| h3          | Display  | `clamp(1.25rem, 3vw, 1.6rem)`         | |
| Body        | Body     | `1rem` / line-height 1.6              | prose capped **65–75ch** |
| Chat message| Body     | `1rem` / 1.55                          | |
| Small/meta  | Body     | `0.85rem`                              | timestamps, labels |

Use `text-wrap: pretty` on long assistant prose. Do **not** set body copy in Shantell.

---

## 4. Layout (mobile-first)

Chat is the hero (this is *me-as-a-**service***); the profile is the zine cover framing it.

### 4.1 Mobile (< 768px) — single column, stacked
```
┌──────────────────────────┐
│  PROFILE HEADER          │  avatar(doodle frame) + name + headline
│  [gh] [in]  ( Connect )  │  hand-drawn socials + accent button
├──────────────────────────┤
│  CHAT PANEL (dominant)   │  scrollable MessageList, grows to fill
│   · assistant bubble     │
│   · user bubble          │
│  [ starter chips ]       │  shown when empty
├──────────────────────────┤
│  COMPOSER (sticky bottom)│  textarea + vermilion Send; safe-area inset
└──────────────────────────┘
```

### 4.2 Desktop (≥ 1024px) — two-panel "spread"
```
┌───────────────┬───────────────────────────────┐
│ PROFILE PANEL │  CHAT PANEL                     │
│ (sticky,      │   MessageList (scrolls)         │
│  ~38%,        │   ...                           │
│  the "cover") │   ─────────────────────────     │
│ avatar        │   Composer (sticky within col)  │
│ name/headline │                                 │
│ short bio     │                                 │
│ socials       │                                 │
│ ( Connect )   │                                 │
└───────────────┴───────────────────────────────┘
   max-width ~1200–1280px, centered on paper; a thin ink page-frame
   (border + hard shadow) makes the whole thing feel like a physical booklet.
```

- Breakpoints: base (mobile) → `768px` (tablet: more air) → `1024px` (two-panel).
- Grid for the 2-panel spread; flex for 1-D rows (header, composer). No Grid-by-default.
- Test **every heading string at every breakpoint** — long words + big clamps overflow;
  reduce clamp max or rewrite copy rather than let text spill (banned).

---

## 5. Components

Data-driven from `src/content/profile.ts`; no hardcoded copy in components.

| Component | Purpose | Notes |
|---|---|---|
| `AppShell` | Paper bg + page-frame + responsive layout container | Optional very-subtle paper grain (CSS, cheap). |
| `ProfilePanel` | Avatar, name, headline, bio, socials, Connect CTA | Sticky on desktop; collapses to `ProfileHeader` on mobile. |
| `Avatar` | Photo/initial inside a **hand-drawn doodle frame** | SVG wobble ring in `currentColor`. |
| `SocialLinks` | GitHub + LinkedIn as **hand-drawn doodle icons** | Ink stroke; vermilion on hover; real `href`s from profile. |
| `ChatPanel` | Header + `MessageList` + `Composer` | Owns chat state + the stream hook. |
| `MessageList` | Renders messages; auto-scrolls; `aria-live="polite"` | Streaming caret on the in-flight assistant msg. |
| `Message` | One bubble (user vs assistant), **hand-drawn bubble border** | Assistant markdown via `react-markdown` + `remark-gfm`, sanitized. Assistant gets a mini doodle mark. |
| `Composer` | Auto-resize textarea + Send | Enforce **maxLength 2000** (matches backend); disable while streaming; Enter=send, Shift+Enter=newline. |
| `StarterQuestions` | Tappable starter chips (empty state) | From `profile.starters`; Shantell labels; doodle arrow. |
| `ConnectForm` | Name + email → future `POST /api/leads` | Native `<dialog>`; triggered by Connect button now, by `capture_lead` tool event later (§6.4). Client validation + inline errors. |
| `LimitNotice` | Rate-limit reached (HTTP 429) | Zine "out of ink" doodle; shown when backend adds 429 (Phase 6). |
| `doodles/*` | Reusable inline-SVG doodle set | See §7. |

### 5.1 Button pattern (the neo-brutal press)
```css
.btn {
  font-family: var(--font-body); font-weight: 700;
  background: var(--accent); color: var(--on-accent);
  border: var(--border-w) solid var(--ink); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: var(--s-3) var(--s-5);
  transition: transform var(--dur-fast) var(--ease-out),
              box-shadow var(--dur-fast) var(--ease-out);
}
.btn:hover  { background: var(--accent-deep); }
.btn:active { transform: translate(4px, 4px); box-shadow: 0 0 0 0 var(--ink); } /* press = shadow collapse */
.btn:focus-visible { outline: 3px solid var(--ink); outline-offset: 3px; }
@media (prefers-reduced-motion: reduce) { .btn { transition: none; } .btn:active { transform: none; } }
```

---

## 6. API Integration (SSE)

Backend contract (see `TECHNICAL_SPEC.md` §8 and `backend/app/routers/chat.py`):

- **`GET /api/health`** → `{ "status": "ok", "version": "x.y.z" }`.
- **`POST /api/chat`** → `text/event-stream`. Body `{ message: string(1..2000), history: {role,content}[] }`.
  *(`history` is accepted by the model but not yet used server-side — send it anyway for
  forward-compat.)* Sets an httpOnly `sid` cookie → **`credentials: 'include'` is required**.
- **SSE events:** `token` `{ text }` (append delta) · `done` `{}` (end) · `error`
  `{ message }` (show inline, stop stream). Rate-limit `429` + `LimitNotice` arrive in Phase 6.

### 6.1 Stream client (EventSource can't POST — use fetch + ReadableStream)
```ts
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function* streamChat(
  message: string, history: Msg[], signal: AbortSignal,
): AsyncGenerator<{ event: string; data: any }> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
    credentials: "include",
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`chat ${res.status}`);

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += value;
    const frames = buf.split("\n\n");
    buf = frames.pop() ?? "";            // keep trailing partial frame
    for (const frame of frames) {
      let event = "message", data: any = {};
      for (const line of frame.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7);
        else if (line.startsWith("data: ")) data = JSON.parse(line.slice(6));
      }
      yield { event, data };
    }
  }
}
```

### 6.2 `useChatStream` hook (behavioral contract)
- State: `messages`, `status` (`idle | streaming | error`), `send(text)`, `stop()`.
- On `send`: push user msg + an empty assistant msg; iterate `streamChat`; on `token`
  append `data.text`; on `error` mark the assistant msg errored + set `status="error"`;
  on `done`/generator-end set `idle`. Keep an `AbortController` for `stop()` / unmount.
- Show a Shantell **"…thinking"** doodle tag between send and first token (retrieval latency).

### 6.4 `capture_lead` (future)
When the backend adds the `capture_lead` tool, it will emit a `tool` SSE event; the client
opens `ConnectForm` prefilled. Until then, `ConnectForm` is opened only by the Connect button.

---

## 7. Doodle System (the signature)

**Inline SVG React components** in `src/components/doodles/` — self-contained, themeable,
animatable. Rules:

- `stroke="currentColor"`, `fill="none"` (or `var(--accent)` for pops); `stroke-width: 2–3`;
  `stroke-linecap: round`; `stroke-linejoin: round`. Slightly **irregular paths** (hand feel).
- Set color via CSS `color` on a wrapper; hover → `color: var(--accent)`.
- Accessibility: decorative doodles `aria-hidden="true"`; meaningful ones (social links) get
  `role="img"` + `<title>`.
- **Hero draw-on:** animate `stroke-dashoffset` 0→full once on load; disabled under
  `prefers-reduced-motion`. Never gate content visibility on the animation.

Set to author: `AvatarRing`, `Squiggle` (underline), `ArrowScribble`, `Sparkle`, `BubbleTail`,
`GithubDoodle`, `LinkedinDoodle`, `SendDoodle`, `OutOfInk` (limit notice).

```tsx
// Squiggle underline — currentColor, hand-drawn
export const Squiggle = (p: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 120 12" fill="none" aria-hidden {...p}>
    <path d="M2 7c14-8 26 6 40 0s26-8 40-2 24 6 36 1"
      stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
  </svg>
);
```

---

## 8. Motion

Purposeful, not decorative; every animation has a `prefers-reduced-motion` fallback.

- **Message entrance:** staggered slide+fade (8px, `--ease-out`), per message — legitimate
  list stagger, not a uniform page reflex.
- **Streaming caret:** blinking ink block at the tail of the in-flight message.
- **Button press:** shadow-collapse + translate (§5.1).
- **Hero doodles:** one draw-on stroke reveal on load.
- **Reduced motion:** crossfade or instant; caret becomes static; doodles render final state.
- Don't animate layout props (width/height/top). Use transform/opacity + clip/mask.

---

## 9. Accessibility (WCAG AA)

- Contrast per §2.1 (the vermilion rule is the main hazard).
- Visible focus everywhere: `outline: 3px solid var(--ink); outline-offset: 3px` (the ink
  outline reads as brutalist, not as a bolt-on).
- Landmarks: `<header>` (profile), `<main>` (chat), `<form>` (composer, connect). Labeled
  inputs. `aria-live="polite"` on the message list so streamed text is announced (throttled).
- Full keyboard path: starters (buttons), composer (Enter/Shift+Enter), dialog focus-trap +
  Esc, logical tab order.
- Respect `prefers-reduced-motion` (§8). Target sizes ≥44px on mobile.

---

## 10. Tech Stack & Structure

- **Vite + React + TypeScript** SPA (Vercel host). Node ≥ 20.
- **Fonts:** `@fontsource-variable/shantell-sans`, `@fontsource-variable/hanken-grotesk`.
- **Markdown:** `react-markdown` + `remark-gfm` (assistant output; sanitized, no raw HTML).
- **Styling:** CSS Modules or plain CSS with the tokens in §2 (no utility-first framework
  required; keep the brutalist CSS legible). Motion via CSS; reach for `motion`/`gsap` only
  if a doodle sequence needs it.
- **State:** local React state + the `useChatStream` hook; no global store needed for v1.
- **Env:** `VITE_API_BASE` (backend origin). Committed `.env.example`.
- **Testing:** Vitest + React Testing Library — stream render (mock `streamChat`), composer
  validation/limit, ConnectForm validation, starter → send, reduced-motion smoke.

```
frontend/
  index.html
  package.json  vite.config.ts  tsconfig.json  .env.example
  src/
    main.tsx  App.tsx
    styles/     tokens.css  global.css
    content/    profile.ts            # name, headline, bio, avatar, socials, starters
    lib/        streamChat.ts  useChatStream.ts  api.ts
    components/
      AppShell.tsx
      profile/  ProfilePanel.tsx  ProfileHeader.tsx  Avatar.tsx  SocialLinks.tsx
      chat/     ChatPanel.tsx  MessageList.tsx  Message.tsx  Composer.tsx  StarterQuestions.tsx
      connect/  ConnectForm.tsx
      system/   LimitNotice.tsx  ErrorNotice.tsx
      doodles/  index.tsx  (AvatarRing, Squiggle, ArrowScribble, Sparkle, BubbleTail,
                            GithubDoodle, LinkedinDoodle, SendDoodle, OutOfInk)
    test/       setup.ts  *.test.tsx
```

### 10.1 `profile.ts` shape
```ts
export const profile = {
  name: "Arindam Mondal",
  headline: "Lead Full Stack Developer · building agentic AI & RAG",
  avatar: "/avatar.jpg",              // owner to supply; fallback = initials in doodle ring
  bio: "12+ years shipping enterprise platforms. Currently leading a next-gen fraud-detection platform at FICO. Ask my AI twin anything.",
  socials: [
    { kind: "github",   href: "https://github.com/Arindam-Mondal" },
    { kind: "linkedin", href: "https://linkedin.com/in/amond" },
  ],
  starters: [
    "What are Arindam's skills?",
    "What is he building at FICO?",
    "Tell me about the Cougar low-code framework.",
    "What is he looking for next?",
  ],
} as const;
```

---

## 11. Build Order (Phase 8 slices)

1. **Scaffold** — Vite+TS, fonts, `tokens.css`/`global.css`, `AppShell` + page-frame,
   `profile.ts`. Verify paper+ink+vermilion render at all breakpoints.
2. **Doodle kit** — author the SVG set (§7) with the hero draw-on.
3. **ProfilePanel/Header** — avatar+doodle frame, socials, Connect button (opens empty dialog).
4. **ChatPanel** — `streamChat` + `useChatStream`; MessageList/Message/Composer; starters;
   wire to live backend (`VITE_API_BASE`). **Verify real SSE stream end-to-end.**
5. **ConnectForm** — validation now; `capture_lead` trigger later.
6. **States & polish** — error/limit notices, reduced-motion, a11y pass, responsive QA,
   `impeccable audit` + `polish`.
7. **Tests** — Vitest suite (§10).

---

## 12. Design Workflow (which skills to use)

**Always drive UI craft through the skills — don't freehand it.**

- **`impeccable`** — the design system + craft engine. `shape` a screen before building,
  `craft` to build end-to-end, then `critique` / `audit` / `polish` before shipping. It
  enforces contrast, the slop bans, motion, and responsive rules referenced throughout here.
- **`frontend-design`** — aesthetic direction / distinctive visual choices when a surface
  needs a stronger POV; keeps the zine voice from drifting into templated defaults.
- **Theme source of truth:** [`.claude/skills/zine-theme/SKILL.md`](./.claude/skills/zine-theme/SKILL.md)
  — tokens, fonts, doodle rules, Do/Don't. Load it whenever touching this UI.

---

## 13. Open Items (owner)

- Avatar image (square, ≥512px). Fallback = initials in a doodle ring.
- Confirm the 3–5 starter questions in `profile.ts`.
- Confirm headline/bio microcopy (draft above from `content/about.md`).
- Optional: a short doodle-friendly logotype / signature for the profile header.
