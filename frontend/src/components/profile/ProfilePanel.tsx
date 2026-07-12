import { Avatar } from "./Avatar";
import { SocialLinks } from "./SocialLinks";
import { Squiggle } from "../doodles";
import { profile } from "../../content/profile";

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
      <p className="profile__bio prose">{profile.bio}</p>

      <div className="profile__actions">
        <button type="button" className="btn" onClick={onConnect}>
          Connect with me
        </button>
        <SocialLinks />
      </div>
    </header>
  );
}
