import { useLayoutEffect, useRef, useState } from "react";
import { SendDoodle } from "../doodles";
import type { ChatStatus } from "../../lib/useChatStream";

const MAX = 2000; // matches backend ChatRequest validation

type Props = {
  status: ChatStatus;
  onSend: (text: string) => void;
};

/** Auto-resizing textarea + Send. Enter sends, Shift+Enter newlines. */
export function Composer({ status, onSend }: Props) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const busy = status === "thinking" || status === "streaming";

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const submit = () => {
    const text = value.trim();
    if (!text || busy) return;
    onSend(text);
    setValue("");
  };

  return (
    <form
      className="composer"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      {value.length > MAX * 0.75 && (
        <span className="composer__count">
          {value.length}/{MAX}
        </span>
      )}
      <textarea
        ref={ref}
        className="composer__field"
        value={value}
        maxLength={MAX}
        rows={1}
        placeholder="Ask about Arindam's work, skills, projects…"
        aria-label="Ask a question"
        disabled={status === "limited"}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
      />
      <button
        type="submit"
        className="btn composer__send"
        disabled={busy || !value.trim() || status === "limited"}
        aria-label="Send"
      >
        <SendDoodle width={22} height={22} style={{ color: "var(--on-accent)" }} />
      </button>
    </form>
  );
}
