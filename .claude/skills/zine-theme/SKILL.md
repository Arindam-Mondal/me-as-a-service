---
name: zine-theme
description: Use when building, styling, or reviewing ANY frontend UI for the Me-as-a-Service portfolio — the "Tactile Neo-Brutalism / Zine" theme (beige paper base, heavy black ink outlines + hard offset shadows, one Riso-Vermilion accent, and hand-drawn doodle overlays). Provides the design tokens, fonts, doodle system, component patterns, and Do/Don't. Mobile-first, light-only, WCAG AA. Points to the impeccable + frontend-design skills for craft.
---

# Zine Theme — Tactile Neo-Brutalism for Me-as-a-Service

The visual identity for the public UI: a **human-made indie zine wrapped around a custom AI
chat engine**. Raw, tactile, personal — deliberately *not* a uniform AI interface. Full
build spec: [`UI_TECHNICAL_SPEC.md`](../../../UI_TECHNICAL_SPEC.md).

## When to use
Any time you create, restyle, or review frontend code for this project (`frontend/**`), pick
colors/fonts/spacing, add a component, or judge whether a screen is on-brand.

## Companion skills (use these for craft — don't freehand)
- **`impeccable`** — design-system + craft engine. `shape` before building, `craft` to build,
  `critique` / `audit` / `polish` before shipping. Enforces contrast, slop-bans, motion,
  responsive. This theme obeys it.
- **`frontend-design`** — aesthetic direction when a surface needs a stronger POV; keeps the
  zine voice from sliding into templated defaults.

## The four pillars (what makes it the zine, not generic beige)
1. **Beige is the *paper*, not the whole palette.** Warm paper base carries nothing on its own.
2. **One loud accent** — Riso Vermilion `#FF4D2E` — for fills, borders, marker-underlines, doodle pops.
3. **Heavy black ink** — 2–3px outlines + **hard offset shadows (no blur)** on tactile elements.
4. **Hand-drawn doodles** replace vector icons — avatar frame, GitHub/LinkedIn marks,
   chat-bubble tails, arrows, squiggles, sparkles. Plus a hand-drawn display face (Shantell Sans).

## Tokens (hex = source of truth)
```
--paper #F4ECD8   --paper-2 #ECE3CC   --paper-edge #E3D8BC
--ink   #141210   --ink-soft #4A443A
--accent #FF4D2E  --accent-deep #D93A1E   --on-accent #141210
--border-w 3px    --radius 4px
--shadow 4px 4px 0 0 var(--ink)   --shadow-sm 2px 2px 0 0   --shadow-lg 6px 6px 0 0
--ease-out cubic-bezier(0.22,1,0.36,1)
```
Full token block (spacing, z-scale, motion durations, OKLCH values) is in
`UI_TECHNICAL_SPEC.md` §2. Light-only — no dark theme in v1.

## Typography
- **Display:** Shantell Sans (hand-drawn) — headings, name, chips, doodle labels. Never body copy.
- **Body:** Hanken Grotesk — chat, prose, forms, buttons. Readable where Shantell tires the eye.
- Self-host via `@fontsource-variable/*`. Fluid `clamp()`, ratio ≥1.25, display max ≤6rem,
  letter-spacing ≥ -0.04em, prose 65–75ch.

## Contrast — the one hazard (MUST)
- **Vermilion is NEVER text on paper** (~2.5:1, fails). Use it for fills/borders/underlines/doodle
  strokes only. Links = **ink text + vermilion marker underline**.
- **Text on a vermilion fill = ink `#141210`, bold** (≈4.4:1). No white-on-vermilion below large-bold.
- Body = `--ink`, secondary = `--ink-soft` (both ≥4.5:1 on paper). Placeholders use `--ink-soft`.

## Doodles
Inline SVG components (`src/components/doodles/`): `stroke="currentColor"`, `fill:none`,
width 2–3, round caps/joins, slightly irregular paths. Color via wrapper `color`; hover →
`var(--accent)`. Decorative = `aria-hidden`; meaningful = `role="img"` + `<title>`. Hero
draw-on via `stroke-dashoffset`, disabled under reduced motion.

## Signature button
Vermilion fill + ink border + hard shadow; **press = shadow-collapse + `translate(4px,4px)`**;
`:focus-visible` = `3px solid var(--ink)` offset 3px; reduced-motion removes the transform.

## Do
- Mobile-first; chat is the hero, profile is the "cover." Two-panel spread ≥1024px.
- Vary spacing for rhythm; wrap the whole thing in a thin ink page-frame (feels like a booklet).
- `prefers-reduced-motion` fallback on every animation; `aria-live="polite"` for streamed text.
- Test heading strings at every breakpoint (no overflow).

## Don't (AI-slop bans — auto-reject)
- ❌ Gradient text · ❌ glassmorphism · ❌ side-stripe (`border-left`) accents · ❌ tiny uppercase
  tracked eyebrows above every section · ❌ numbered `01/02/03` section scaffolding ·
  ❌ identical icon-heading-text card grids · ❌ hero-metric template · ❌ vermilion body text ·
  ❌ light-gray body text "for elegance" · ❌ generic vector icons where a doodle belongs ·
  ❌ Shantell Sans for body copy · ❌ text overflowing its container at any breakpoint.

## Slop test
If someone could say "an AI made this" without hesitation, it failed. The doodles + hard ink +
committed vermilion + hand-drawn type are what make it read "a *person* made this."
