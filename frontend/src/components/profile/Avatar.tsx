import { useState } from "react";
import { AvatarRing } from "../doodles";
import { profile } from "../../content/profile";

/** Avatar inside a hand-drawn doodle ring; falls back to initials if the image is missing. */
export function Avatar() {
  const [broken, setBroken] = useState(false);
  const showImg = Boolean(profile.avatar) && !broken;

  return (
    <div className="avatar">
      <AvatarRing className="avatar__ring draw" style={{ ["--len" as string]: 320 }} />
      {showImg ? (
        <img
          className="avatar__img"
          src={profile.avatar}
          alt={`${profile.name}, hand-drawn portrait`}
          onError={() => setBroken(true)}
        />
      ) : (
        <span className="avatar__fallback" aria-label={profile.name}>
          {profile.initials}
        </span>
      )}
    </div>
  );
}
