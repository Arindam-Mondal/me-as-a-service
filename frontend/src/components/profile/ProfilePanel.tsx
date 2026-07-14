import type { CSSProperties, ReactNode } from "react";
import { Avatar } from "./Avatar";
import { SocialLinks } from "./SocialLinks";
import { Squiggle } from "../doodles";
import { profile } from "../../content/profile";

const escapeRegExp = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** Split the bio on the configured highlight terms and wrap each match in a
    marker-swipe <mark>. `--mark-i` staggers the swipe-on animation. */
function highlightBio(text: string, terms: readonly string[]): ReactNode[] {
  if (terms.length === 0) return [text];
  const re = new RegExp(`(${terms.map(escapeRegExp).join("|")})`, "g");
  let hit = 0;
  return text.split(re).map((part, i) =>
    terms.includes(part) ? (
      <mark key={i} className="mark" style={{ "--mark-i": hit++ } as CSSProperties}>
        {part}
      </mark>
    ) : (
      part
    ),
  );
}

/** The "zine cover": avatar, name, headline, bio, socials, and the Connect CTA.
    Sticky sidebar on desktop, stacked header on mobile. */
export function ProfilePanel({ onConnect }: { onConnect: () => void }) {
  return (
    <header className="profile">
      <div className="profile__top">
        <Avatar />
        <div>
          <h1 className="profile__name">{profile.name}</h1>
          <Squiggle
            width={132}
            height={12}
            style={{ color: "var(--accent)", marginTop: 4 }}
            aria-hidden
          />
        </div>
      </div>

      <p className="profile__headline">{profile.headline}</p>
      <p className="profile__bio prose">{highlightBio(profile.bio, profile.bioHighlights)}</p>

      <div className="profile__actions">
        <button type="button" className="btn" onClick={onConnect}>
          Connect with me
        </button>
        <SocialLinks />
      </div>
    </header>
  );
}
