import { ArrowScribble, Sparkle } from "../doodles";
import { profile } from "../../content/profile";

/** Empty-state starter chips. */
export function StarterQuestions({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="empty">
      <p className="empty__lead">
        <Sparkle
          width={20}
          height={20}
          style={{ color: "var(--accent)", display: "inline-block", verticalAlign: "-3px" }}
        />{" "}
        Hi — I'm Arindam's AI twin. Ask me anything about his work.
      </p>
      <div className="starters__row">
        <ArrowScribble width={26} height={26} />
        <span>try one of these</span>
      </div>
      <div className="starters">
        {profile.starters.map((q) => (
          <button key={q} type="button" className="chip" onClick={() => onPick(q)}>
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
