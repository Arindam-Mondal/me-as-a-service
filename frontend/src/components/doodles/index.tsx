/* Hand-drawn doodle kit — inline SVG, stroke=currentColor, slightly irregular paths.
   Decorative doodles are aria-hidden; meaningful ones (socials) get role+title. */
import type { SVGProps } from "react";

type Props = SVGProps<SVGSVGElement>;

const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2.4,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

/** Wobbly ring drawn around the avatar. */
export function AvatarRing(props: Props) {
  return (
    <svg viewBox="0 0 92 92" aria-hidden {...props}>
      <path
        {...base}
        d="M46 5c14-1 30 8 38 22 6 11 4 27-6 38-9 10-25 15-39 12C24 74 10 63 7 48 4 33 12 18 26 10c6-4 13-5 20-5Z"
      />
    </svg>
  );
}

/** Marker squiggle underline. */
export function Squiggle(props: Props) {
  return (
    <svg viewBox="0 0 120 12" aria-hidden {...props}>
      <path {...base} strokeWidth={3} d="M2 7c14-8 26 6 40 0s26-8 40-2 24 6 36 1" />
    </svg>
  );
}

/** Hand-drawn arrow pointing down-right toward the starter chips. */
export function ArrowScribble(props: Props) {
  return (
    <svg viewBox="0 0 40 40" aria-hidden {...props}>
      <path {...base} d="M6 6c4 12 12 22 26 27" />
      <path {...base} d="M22 33l10 0M32 33l0-10" />
    </svg>
  );
}

/** Little 4-point sparkle. */
export function Sparkle(props: Props) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden {...props}>
      <path {...base} d="M12 2c1 6 4 9 10 10-6 1-9 4-10 10-1-6-4-9-10-10 6-1 9-4 10-10Z" />
    </svg>
  );
}

/** Assistant chat mark — a scribbled speech bubble. */
export function BubbleMark(props: Props) {
  return (
    <svg viewBox="0 0 34 34" aria-hidden {...props}>
      <path {...base} d="M5 7c8-2 17-2 24 1 3 5 3 12-1 16-4 3-11 4-17 2l-7 4 2-8c-4-4-4-11-1-15Z" />
      <path {...base} strokeWidth={2} d="M12 15h11M12 20h7" />
    </svg>
  );
}

/** Hand-drawn GitHub cat-ish mark. */
export function GithubDoodle(props: Props) {
  return (
    <svg viewBox="0 0 32 32" role="img" {...props}>
      <title>GitHub</title>
      <path
        {...base}
        d="M16 4C9 4 4 9 4 16c0 5 3 9 8 11 1 0 1-.5 1-1v-2c-3 .6-4-1-4-1-.6-1.4-1.4-1.8-1.4-1.8-1-.7 0-.7 0-.7 1 .1 1.6 1.1 1.6 1.1 1 1.7 2.6 1.2 3.2.9.1-.7.4-1.2.7-1.5-2.4-.3-5-1.2-5-5.3 0-1.2.4-2.1 1.1-2.9-.1-.3-.5-1.4.1-2.9 0 0 .9-.3 3 1.1a10 10 0 0 1 5.4 0c2.1-1.4 3-1.1 3-1.1.6 1.5.2 2.6.1 2.9.7.8 1.1 1.7 1.1 2.9 0 4.1-2.6 5-5 5.3.4.4.8 1.1.8 2.2v3.3c0 .5 0 1 1 1 5-2 8-6 8-11 0-7-5-12-12-12Z"
      />
    </svg>
  );
}

/** Hand-drawn LinkedIn mark. */
export function LinkedinDoodle(props: Props) {
  return (
    <svg viewBox="0 0 32 32" role="img" {...props}>
      <title>LinkedIn</title>
      <rect {...base} x="4" y="4" width="24" height="24" rx="4" />
      <path {...base} d="M10 14v8" />
      <circle cx="10" cy="10" r="1.4" fill="currentColor" stroke="none" />
      <path {...base} d="M15 22v-5c0-2 1-3 3-3s3 1 3 3v5M15 14v8" />
    </svg>
  );
}

/** Paper-plane send doodle. */
export function SendDoodle(props: Props) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden {...props}>
      <path {...base} d="M3 12l17-8-6 17-3-6-8-3Z" />
      <path {...base} d="M11 13l4-4" />
    </svg>
  );
}

/** Circular-arrow reset doodle for "start over". */
export function RefreshDoodle(props: Props) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden {...props}>
      <path {...base} d="M20 12a8 8 0 1 1-2.4-5.7" />
      <path {...base} d="M20 3.6V8h-4.3" />
    </svg>
  );
}

/** "Out of ink" splotch for the rate-limit notice. */
export function OutOfInk(props: Props) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden {...props}>
      <path {...base} d="M16 3c3 6 8 9 8 15a8 8 0 0 1-16 0c0-6 5-9 8-15Z" />
      <path {...base} strokeWidth={2} d="M12 19c0 2 1.5 3 3 3" />
    </svg>
  );
}
