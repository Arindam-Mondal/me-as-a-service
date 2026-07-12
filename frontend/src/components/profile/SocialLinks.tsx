import { GithubDoodle, LinkedinDoodle } from "../doodles";
import { profile, type Social } from "../../content/profile";

const icon = (kind: Social["kind"]) =>
  kind === "github" ? (
    <GithubDoodle width={24} height={24} />
  ) : (
    <LinkedinDoodle width={24} height={24} />
  );

/** Hand-drawn social links. */
export function SocialLinks() {
  return (
    <nav className="socials" aria-label="Social links">
      {profile.socials.map((s) => (
        <a
          key={s.kind}
          className="socials__link"
          href={s.href}
          target="_blank"
          rel="noreferrer noopener"
          aria-label={s.label}
        >
          {icon(s.kind)}
        </a>
      ))}
    </nav>
  );
}
