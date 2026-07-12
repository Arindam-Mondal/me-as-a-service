import { OutOfInk } from "../doodles";

/** Shown when the backend rate-limit (HTTP 429) is hit (Phase 6). */
export function LimitNotice() {
  return (
    <div className="notice notice--limit" role="status">
      <span style={{ color: "var(--warn)" }} aria-hidden>
        <OutOfInk width={26} height={26} />
      </span>
      <span>
        Out of ink for now — you've hit the question limit. Try again later, or use{" "}
        <strong>Connect with me</strong> to reach Arindam directly.
      </span>
    </div>
  );
}
